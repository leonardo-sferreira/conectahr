// Motor de resolucao de regras (item 4.11): dado um colaborador e um
// parametro, resolve o valor efetivo considerando, nesta ordem
// (spec.md - "Abrangencia e resolucao de regras"): matriz do contrato,
// norma vigente, instrumento coletivo, regra de cargo/departamento e
// excecao individual. Cada nivel so substitui o anterior quando ha uma
// regra_override vigente aplicavel; o nivel mais especifico vence.
//
// Mapeamento de nivel: colaborador=5 (excecao individual);
// cargo/departamento=4; instrumento coletivo (acordo_coletivo,
// convencao_coletiva, termo_aditivo)=3; demais escopos com override
// vigente (empresa, estabelecimento, estado, municipio, tipo_contrato,
// categoria_profissional — tratados como "norma vigente")=2; sem
// override aplicavel=1 (so a matriz regra_contrato).
//
// Simplificacoes assumidas (colaborador nao tem esses campos no
// cadastro): abrangencia "estabelecimento" sempre aplica (equivalente a
// empresa); abrangencia "categoria_profissional" nunca aplica (nenhum
// campo correspondente em colaborador para comparar); "estado"/
// "municipio" comparam contra o endereco pessoal do colaborador
// (colaborador.estado/colaborador.cidade), nao um local de trabalho
// dedicado (nao existe esse conceito no modelo atual).
//
// Conflito (spec.md - "Conflito juridico"): quando ha mais de uma regra
// vigente aplicavel no nivel mais especifico encontrado, com valores
// diferentes e prioridade empatada, retorna conflito=true e nao resolve
// automaticamente — cabe a RH decidir.
function "ConectaHR/resolver_regra" {
  input {
    int colaborador_id
    text parametro
  }

  stack {
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador

    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra_base

    db.query regra_override {
      where = $db.regra_override.parametro == $input.parametro && $db.regra_override.status == "vigente" && $db.regra_override.ativo == true && $db.regra_override.data_inicio <= "now" && ($db.regra_override.data_fim == null || $db.regra_override.data_fim >= "now")
      return = {type: "list"}
    } as $candidatos_brutos

    var $nivel_maximo {
      value = 0
    }

    var $candidatos_validos {
      value = []
    }

    foreach ($candidatos_brutos) {
      each as $cand {
        // Determina se este candidato se aplica ao colaborador, um
        // abrangencia por vez (mais seguro do que um unico ternario
        // gigante). "categoria_profissional" nunca aplica — colaborador
        // nao tem esse campo no cadastro (gap documentado no cabecalho).
        var $aplica {
          value = false
        }

        conditional {
          if ($cand.abrangencia == "empresa" || $cand.abrangencia == "estabelecimento") {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($cand.abrangencia == "estado" && $colaborador.estado != null && $cand.estado != null && $colaborador.estado == $cand.estado) {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($cand.abrangencia == "municipio" && $colaborador.cidade != null && $cand.municipio != null && $colaborador.cidade == $cand.municipio) {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($cand.abrangencia == "tipo_contrato" && $cand.tipo_contrato != null && $colaborador.tipo_contrato == $cand.tipo_contrato) {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($cand.abrangencia == "departamento" && $cand.departamento_id != null && $colaborador.departamento_id == $cand.departamento_id) {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($cand.abrangencia == "cargo" && $cand.cargo_id != null && $colaborador.cargo_id == $cand.cargo_id) {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($cand.abrangencia == "colaborador" && $cand.colaborador_id != null && $colaborador.id == $cand.colaborador_id) {
            var.update $aplica {
              value = true
            }
          }
        }

        conditional {
          if ($aplica) {
            var $nivel_cand {
              value = ($cand.abrangencia == "colaborador" ? 5 : (($cand.abrangencia == "cargo" || $cand.abrangencia == "departamento") ? 4 : null))
            }

            conditional {
              if ($nivel_cand == null) {
                db.get instrumento_normativo {
                  field_name = "id"
                  field_value = $cand.instrumento_normativo_id
                } as $instrumento_do_cand

                var $eh_coletivo {
                  value = ($instrumento_do_cand != null && ($instrumento_do_cand.tipo == "acordo_coletivo" || $instrumento_do_cand.tipo == "convencao_coletiva" || $instrumento_do_cand.tipo == "termo_aditivo"))
                }

                var.update $nivel_cand {
                  value = ($eh_coletivo ? 3 : 2)
                }
              }
            }

            var.update $candidatos_validos {
              value = $candidatos_validos|push:{
                id             : $cand.id
                nivel          : $nivel_cand
                valor_novo     : $cand.valor_novo
                prioridade     : $cand.prioridade
                abrangencia    : $cand.abrangencia
                instrumento_id : $cand.instrumento_normativo_id
              }
            }

            conditional {
              if ($nivel_cand > $nivel_maximo) {
                var.update $nivel_maximo {
                  value = $nivel_cand
                }
              }
            }
          }
        }
      }
    }

    // Filtra os candidatos no nivel mais especifico encontrado e apura a maior prioridade entre eles.
    var $candidatos_no_topo {
      value = []
    }

    var $prioridade_maxima_no_topo {
      value = -2147483648
    }

    foreach ($candidatos_validos) {
      each as $cv {
        conditional {
          if ($cv.nivel == $nivel_maximo) {
            var.update $candidatos_no_topo {
              value = $candidatos_no_topo|push:$cv
            }

            conditional {
              if ($cv.prioridade > $prioridade_maxima_no_topo) {
                var.update $prioridade_maxima_no_topo {
                  value = $cv.prioridade
                }
              }
            }
          }
        }
      }
    }

    // Entre os empatados na maior prioridade do nivel mais especifico,
    // verifica se ha conflito real (valores diferentes) ou se e so
    // redundancia (mesmo valor).
    var $override_vencedor_id {
      value = null
    }

    var $valor_vencedor {
      value = null
    }

    var $conflito {
      value = false
    }

    foreach ($candidatos_no_topo) {
      each as $ct {
        conditional {
          if ($ct.prioridade == $prioridade_maxima_no_topo) {
            conditional {
              if ($override_vencedor_id == null) {
                var.update $override_vencedor_id {
                  value = $ct.id
                }

                var.update $valor_vencedor {
                  value = $ct.valor_novo
                }
              }
            }

            conditional {
              if ($override_vencedor_id != null && $ct.valor_novo != $valor_vencedor) {
                var.update $conflito {
                  value = true
                }
              }
            }
          }
        }
      }
    }

    // So busca o registro completo do vencedor depois de decidido —
    // evita empilhar um objeto aninhado dentro de outro objeto durante
    // os loops acima (padrao nao testado neste workspace).
    var $override_vencedor {
      value = null
    }

    conditional {
      if ($override_vencedor_id != null) {
        db.get regra_override {
          field_name = "id"
          field_value = $override_vencedor_id
        } as $override_vencedor_encontrado

        var.update $override_vencedor {
          value = $override_vencedor_encontrado
        }
      }
    }

    var $nivel_resolvido {
      value = ($override_vencedor_id != null ? $nivel_maximo : 1)
    }

    var $regra_base_id {
      value = ($regra_base != null ? $regra_base.id : null)
    }
  }

  response = {
    nivel_resolvido      : $nivel_resolvido
    regra_contrato_id    : $regra_base_id
    regra_contrato       : $regra_base
    override_aplicado    : $override_vencedor
    conflito             : $conflito
    candidatos_no_topo   : $candidatos_no_topo
  }

  tags = ["conectahr"]
  guid = "conectahr-resolver-regra-0001"
}
