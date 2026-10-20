// Impacto de uma regra de override (change tela-de-regras, D1): as pessoas ativas atingidas pela
// abrangencia (a mesma logica que estava na simulacao) e os conflitos com regras vigentes.
// Conflito = outra regra vigente do mesmo parametro e da mesma prioridade, com valor diferente,
// vigencia que se sobrepoe e pelo menos uma pessoa atingida em comum. A pessoa em comum e conferida
// pessoa a pessoa contra a abrangencia da outra regra, sem chamar outra funcao.
function "ConectaHR/impacto_override" {
  input {
    int override_id
  }

  stack {
    db.get regra_override {
      field_name = "id"
      field_value = $input.override_id
    } as $override

    // Levanta os colaboradores afetados pela abrangencia do override,
    // um caso por vez. "categoria_profissional" nunca resolve populacao
    // — mesmo gap documentado no resolver_regra (colaborador nao tem
    // esse campo). "estabelecimento" tratado como empresa inteira.
    var $colaboradores_afetados {
      value = []
    }

    conditional {
      if ($override.abrangencia == "empresa" || $override.abrangencia == "estabelecimento") {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo"
          return = {type: "list"}
        } as $populacao_empresa

        var.update $colaboradores_afetados {
          value = $populacao_empresa
        }
      }
    }

    conditional {
      if ($override.abrangencia == "estado" && $override.estado != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.estado == $override.estado
          return = {type: "list"}
        } as $populacao_estado

        var.update $colaboradores_afetados {
          value = $populacao_estado
        }
      }
    }

    conditional {
      if ($override.abrangencia == "municipio" && $override.municipio != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.cidade == $override.municipio
          return = {type: "list"}
        } as $populacao_municipio

        var.update $colaboradores_afetados {
          value = $populacao_municipio
        }
      }
    }

    conditional {
      if ($override.abrangencia == "tipo_contrato" && $override.tipo_contrato != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.tipo_contrato == $override.tipo_contrato
          return = {type: "list"}
        } as $populacao_tipo_contrato

        var.update $colaboradores_afetados {
          value = $populacao_tipo_contrato
        }
      }
    }

    conditional {
      if ($override.abrangencia == "departamento" && $override.departamento_id != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.departamento_id == $override.departamento_id
          return = {type: "list"}
        } as $populacao_departamento

        var.update $colaboradores_afetados {
          value = $populacao_departamento
        }
      }
    }

    conditional {
      if ($override.abrangencia == "cargo" && $override.cargo_id != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.cargo_id == $override.cargo_id
          return = {type: "list"}
        } as $populacao_cargo

        var.update $colaboradores_afetados {
          value = $populacao_cargo
        }
      }
    }

    conditional {
      if ($override.abrangencia == "colaborador" && $override.colaborador_id != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.id == $override.colaborador_id
          return = {type: "list"}
        } as $populacao_individual

        var.update $colaboradores_afetados {
          value = $populacao_individual
        }
      }
    }

    var $conflitos {
      value = []
    }

    conditional {
      if ($override != null) {
        db.query regra_override {
          where = $db.regra_override.parametro == $override.parametro && $db.regra_override.status == "vigente" && $db.regra_override.prioridade == $override.prioridade && $db.regra_override.id != $override.id
          return = {type: "list"}
        } as $candidatas

        foreach ($candidatas) {
          each as $cand {
            var $sobrepoe {
              value = ((($override.data_fim == null) || ($cand.data_inicio <= $override.data_fim)) && (($cand.data_fim == null) || ($override.data_inicio <= $cand.data_fim)))
            }

            conditional {
              if ($sobrepoe && ($cand.valor_novo != $override.valor_novo)) {
                var $em_comum {
                  value = 0
                }

                foreach ($colaboradores_afetados) {
                  each as $p {
                    var $atinge {
                      value = (($cand.abrangencia == "empresa") || ($cand.abrangencia == "estabelecimento") || (($cand.abrangencia == "estado") && ($p.estado == $cand.estado)) || (($cand.abrangencia == "municipio") && ($p.cidade == $cand.municipio)) || (($cand.abrangencia == "tipo_contrato") && ($p.tipo_contrato == $cand.tipo_contrato)) || (($cand.abrangencia == "departamento") && ($p.departamento_id == $cand.departamento_id)) || (($cand.abrangencia == "cargo") && ($p.cargo_id == $cand.cargo_id)) || (($cand.abrangencia == "colaborador") && ($p.id == $cand.colaborador_id)))
                    }

                    conditional {
                      if ($atinge) {
                        var.update $em_comum {
                          value = $em_comum + 1
                        }
                      }
                    }
                  }
                }

                conditional {
                  if ($em_comum > 0) {
                    var.update $conflitos {
                      value = $conflitos|push:{id: $cand.id, parametro: $cand.parametro, prioridade: $cand.prioridade, valor_novo: $cand.valor_novo, abrangencia: $cand.abrangencia, departamento_id: $cand.departamento_id, cargo_id: $cand.cargo_id, colaborador_id: $cand.colaborador_id, tipo_contrato: $cand.tipo_contrato, estado: $cand.estado, municipio: $cand.municipio, versao: $cand.versao, data_inicio: $cand.data_inicio, data_fim: $cand.data_fim, pessoas_em_comum: $em_comum}
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    override : $override
    afetados : $colaboradores_afetados
    conflitos: $conflitos
  }

  tags = ["conectahr"]
  guid = "conectahr-impacto-override-0001"
}
