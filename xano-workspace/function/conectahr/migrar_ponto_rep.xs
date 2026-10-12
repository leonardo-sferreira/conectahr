// Migracao do ponto antigo para o REP-P (change ponto-rep-p-e-ferias-clt, tarefa 3.4). Roda so
// pela CLI do Xano (funcoes nao sao expostas por HTTP), uma unica vez.
//   1. Registro tipo 5 "I" para cada colaborador nao desligado e nao anonimizado que ainda nao
//      tem registro de empregado na ARP.
//   2. As marcacoes de registro_ponto vao para a ARP (tipo 7), em ordem cronologica de todas as
//      pessoas. Quando houve correcao aprovada de um campo, o horario original (valor_original)
//      e o que vai para a ARP e a correcao vira tratamento: desconsidera o original e inclui o
//      corrigido; se o campo estava vazio, so a inclusao. Dias que ja tem marcacoes na ARP (do
//      ponto/marcar novo) ficam como estao.
//   3. Recalcula cada dia migrado e grava "migracao_rep_p_concluida" em configuracao.
// Com simular = true, so conta o que faria. A data e hora de gravacao das marcacoes migradas e a
// da migracao (nao a da marcacao), o que fica registrado na auditoria.
function "ConectaHR/migrar_ponto_rep" {
  input {
    bool simular?=true
    int? autor_user_id?
  }

  stack {
    db.query configuracao {
      where = $db.configuracao.chave == "migracao_rep_p_concluida"
      return = {type: "single"}
    } as $ja_migrado

    precondition ($ja_migrado == null) {
      error_type = "inputerror"
      error = "A migracao do ponto para o REP-P ja foi feita."
    }

    // ---------- 1. empregados
    db.query colaborador {
      where = $db.colaborador.anonimizado_em == null
      sort = {colaborador.id: "asc"}
      return = {type: "list"}
    } as $colaboradores

    db.query marcacao_ponto {
      where = $db.marcacao_ponto.tipo_registro == 5
      return = {type: "list"}
      output = ["colaborador_id"]
    } as $registros5

    var $com_registro5 {
      value = ","
    }

    foreach ($registros5) {
      each as $r5 {
        var.update $com_registro5 {
          value = $com_registro5 ~ ($r5.colaborador_id|to_text) ~ ","
        }
      }
    }

    var $empregados_incluidos {
      value = 0
    }

    var $cpf_por_colaborador {
      value = {}
    }

    foreach ($colaboradores) {
      each as $c {
        function.run "ConectaHR/somente_digitos" {
          input = {texto: $c.cpf}
        } as $cpf_c

        var.update $cpf_por_colaborador {
          value = $cpf_por_colaborador|set:($c.id|to_text):$cpf_c
        }

        conditional {
          if (($c.status|trim|to_upper) != "DESLIGADO" && ($com_registro5|contains:("," ~ ($c.id|to_text) ~ ",")) == false) {
            var.update $empregados_incluidos {
              value = $empregados_incluidos + 1
            }

            conditional {
              if ($input.simular == false) {
                function.run "ConectaHR/gravar_registro_rep" {
                  input = {tipo_registro: 5, colaborador_id: $c.id, cpf: $cpf_c, cpf_responsavel: "", responsavel_user_id: $input.autor_user_id, dados: {operacao: "I", nome: $c.nome, origem: "migracao"}}
                } as $r5_criado
              }
            }
          }
        }
      }
    }

    // ---------- 2. marcacoes
    db.query marcacao_ponto {
      where = $db.marcacao_ponto.tipo_registro == 7
      return = {type: "list"}
      output = ["colaborador_id", "data"]
    } as $marcacoes_novas

    var $dias_com_arp {
      value = ","
    }

    foreach ($marcacoes_novas) {
      each as $mn {
        var.update $dias_com_arp {
          value = $dias_com_arp ~ ($mn.colaborador_id|to_text) ~ "|" ~ ($mn.data|format_timestamp:"Y-m-d":"UTC") ~ ","
        }
      }
    }

    db.query registro_ponto {
      sort = {registro_ponto.data: "asc"}
      return = {type: "list"}
    } as $registros

    db.query correcao_ponto {
      where = $db.correcao_ponto.status == "aprovada" && ($db.correcao_ponto.tipo == null || $db.correcao_ponto.tipo == "ajuste_campo")
      sort = {correcao_ponto.id: "asc"}
      return = {type: "list"}
    } as $correcoes

    // Cada marcacao a gravar: {ms, colaborador_id, dia, campo, registro_id}. Cada tratamento:
    // {colaborador_id, dia, tipo, ms_original, ms_novo, motivo, autor, correcao_id}.
    var $a_gravar {
      value = []
    }

    var $tratamentos_a_criar {
      value = []
    }

    var $dias_migrados {
      value = []
    }

    var $dias_pulados {
      value = 0
    }

    var $dia_reg {
      value = ""
    }

    var $campos_do_registro {
      value = []
    }

    var $correcao_do_campo {
      value = null
    }

    var $chave {
      value = ""
    }

    var $atual {
      value = null
    }

    var $ja_no_rep_p {
      value = false
    }

    foreach ($registros) {
      each as $reg {
        // Copia o registro antes dos condicionais: dentro de um "else" a variavel do laco chega
        // nula no XanoScript.
        var.update $atual {
          value = $reg
        }

        var.update $dia_reg {
          value = $reg.data|format_timestamp:"Y-m-d":"UTC"
        }

        var.update $ja_no_rep_p {
          value = ($dias_com_arp|contains:("," ~ ($reg.colaborador_id|to_text) ~ "|" ~ $dia_reg ~ ","))
        }

        conditional {
          if ($ja_no_rep_p) {
            var.update $dias_pulados {
              value = $dias_pulados + 1
            }
          }
        }

        conditional {
          if ($ja_no_rep_p == false) {
            var.update $dias_migrados {
              value = $dias_migrados|push:{colaborador_id: $atual.colaborador_id, dia: $dia_reg}
            }

            var.update $campos_do_registro {
              // Por push: numa lista literal, o XanoScript nao avalia as variaveis.
              value = []|push:{campo: "hora_entrada", v: $atual.hora_entrada}|push:{campo: "inicio_intervalo", v: $atual.inicio_intervalo}|push:{campo: "fim_intervalo", v: $atual.fim_intervalo}|push:{campo: "hora_saida", v: $atual.hora_saida}
            }

            foreach ($campos_do_registro) {
              each as $cv {
                // A correcao aprovada mais recente deste campo, se houver.
                var.update $correcao_do_campo {
                  value = null
                }

                foreach ($correcoes) {
                  each as $co {
                    conditional {
                      if ($co.registro_ponto_id == $atual.id && $co.campo == $cv.campo) {
                        var.update $correcao_do_campo {
                          value = $co
                        }
                      }
                    }
                  }
                }

                conditional {
                  if ($correcao_do_campo == null && $cv.v != null) {
                    var.update $a_gravar {
                      value = $a_gravar|push:{ms: $cv.v, colaborador_id: $atual.colaborador_id, dia: $dia_reg, chave: ""}
                    }
                  }
                }

                conditional {
                  if ($correcao_do_campo != null) {
                    var.update $chave {
                      value = "c" ~ ($correcao_do_campo.id|to_text)
                    }

                    conditional {
                      if ($correcao_do_campo.valor_original != null) {
                        var.update $a_gravar {
                          value = $a_gravar|push:{ms: $correcao_do_campo.valor_original, colaborador_id: $atual.colaborador_id, dia: $dia_reg, chave: $chave}
                        }
                      }
                    }

                    var.update $tratamentos_a_criar {
                      value = $tratamentos_a_criar|push:{colaborador_id: $atual.colaborador_id, dia: $dia_reg, chave: $chave, tinha_original: ($correcao_do_campo.valor_original != null), ms_novo: $correcao_do_campo.valor_solicitado, motivo: ($correcao_do_campo.justificativa|substr:0:150), autor: $correcao_do_campo.decidido_por_user_id, correcao_id: $correcao_do_campo.id}
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    var $ordenadas {
      value = $a_gravar|sort:"ms":"number":true
    }

    // marcacao_id gravada para cada original corrigido: chave -> id.
    var $id_por_chave {
      value = {}
    }

    var $marcacoes_gravadas {
      value = 0
    }

    conditional {
      if ($input.simular == false) {
        foreach ($ordenadas) {
          each as $mg {
            function.run "ConectaHR/gravar_registro_rep" {
              input = {tipo_registro: 7, colaborador_id: $mg.colaborador_id, cpf: ($cpf_por_colaborador|get:($mg.colaborador_id|to_text)), momento_marcacao: $mg.ms}
            } as $gravada

            var.update $marcacoes_gravadas {
              value = $marcacoes_gravadas + 1
            }

            conditional {
              if ($mg.chave != "") {
                var.update $id_por_chave {
                  value = $id_por_chave|set:$mg.chave:$gravada.id
                }
              }
            }
          }
        }

        foreach ($tratamentos_a_criar) {
          each as $tc {
            var $autor {
              value = ($tc.autor != null ? $tc.autor : $input.autor_user_id)
            }

            conditional {
              if ($tc.tinha_original) {
                db.add tratamento_ponto {
                  data = {colaborador_id: $tc.colaborador_id, data: $tc.dia, tipo: "desconsideracao", marcacao_id: ($id_por_chave|get:$tc.chave), motivo: ($tc.motivo != null && ($tc.motivo|strlen) >= 5 ? $tc.motivo : "Correcao aprovada antes do REP-P"), autor_user_id: $autor, correcao_ponto_id: $tc.correcao_id}
                } as $t_desc
              }
            }

            conditional {
              if ($tc.ms_novo != null) {
                db.add tratamento_ponto {
                  data = {colaborador_id: $tc.colaborador_id, data: $tc.dia, tipo: "inclusao", data_hora: $tc.ms_novo, motivo: ($tc.motivo != null && ($tc.motivo|strlen) >= 5 ? $tc.motivo : "Correcao aprovada antes do REP-P"), autor_user_id: $autor, correcao_ponto_id: $tc.correcao_id}
                } as $t_incl
              }
            }
          }
        }

        foreach ($dias_migrados) {
          each as $dm {
            function.run "ConectaHR/atualizar_dia_ponto" {
              input = {colaborador_id: $dm.colaborador_id, data: $dm.dia}
            } as $dia_atualizado
          }
        }

        db.add configuracao {
          data = {chave: "migracao_rep_p_concluida", valor_inteiro: $marcacoes_gravadas, atualizado_por_user_id: $input.autor_user_id, updated_at: "now"}
        } as $marca_migracao

        db.add auditoria {
          data = {
            user_id   : $input.autor_user_id
            acao      : "migrar_ponto_rep_p"
            recurso   : "marcacao_ponto"
            valor_novo: "empregados=" ~ ($empregados_incluidos|to_text) ~ "; marcacoes=" ~ ($marcacoes_gravadas|to_text) ~ "; tratamentos_base=" ~ (($tratamentos_a_criar|count)|to_text) ~ "; dias=" ~ (($dias_migrados|count)|to_text) ~ "; dias_ja_no_rep_p=" ~ ($dias_pulados|to_text) ~ "; gravacao=data da migracao"
            resultado : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    simulacao: $input.simular
    empregados_tipo5: $empregados_incluidos
    marcacoes_tipo7: ($a_gravar|count)
    correcoes_viram_tratamento: ($tratamentos_a_criar|count)
    dias_migrados: ($dias_migrados|count)
    dias_ja_no_rep_p: $dias_pulados
    registros_lidos: ($input.simular ? ($registros|count) : null)
    amostra: ($input.simular ? ($registros|slice:0:5) : null)
    correcoes_aprovadas_lidas: ($input.simular ? ($correcoes|count) : null)
  }

  tags = ["conectahr"]
  guid = "conectahr-migrar-ponto-rep-0001"
}
