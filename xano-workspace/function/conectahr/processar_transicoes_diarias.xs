// Transicoes de status dependentes de data, acionadas manualmente por RH/Admin
// (`rotinas/processar_diarias`). O mesmo codigo serve ao `status_operacional`:
// com `aplicar = false` so conta o que a rotina mudaria, sem gravar nada, entao a
// contagem pendente e a aplicada saem da mesma regra.
//
// Ordem (design D7): 1) desligamentos agendados vencidos, 2) ferias aprovadas
// encerradas, 3) ponto aberto de dias anteriores, 4) instrumentos vigentes com
// vigencia encerrada, 5) status Ferias e 6) status Afastado do colaborador.
// Os desligamentos vem primeiro, para quem acabou de ser desligado nao voltar a
// `Ativo`. Colaborador `Desligado` nunca e reativado.
//
// Idempotente: cada consulta so seleciona registros ainda no estado de origem.
function "ConectaHR/processar_transicoes_diarias" {
  input {
    bool aplicar
    int usuario_id
  }

  stack {
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    var $n_desligamentos {
      value = 0
    }

    var $n_ferias_concluidas {
      value = 0
    }

    var $n_ponto_incompleto {
      value = 0
    }

    var $n_instrumentos_expirados {
      value = 0
    }

    var $n_para_ferias {
      value = 0
    }

    var $n_para_afastado {
      value = 0
    }

    var $n_para_ativo {
      value = 0
    }

    var $n_sessoes_limpas {
      value = 0
    }

    var $n_emails_limpos {
      value = 0
    }

    // Prazos de retencao (docs/lgpd/retencao.md, a confirmar com o juridico). Cada
    // um pode ser trocado por variavel de ambiente, em dias.
    var $dias_sessao {
      value = ($env.SESSAO_RETENCAO_DIAS != null ? ($env.SESSAO_RETENCAO_DIAS|to_int) : 180)
    }

    var $dias_email {
      value = ($env.EMAIL_RETENCAO_DIAS != null ? ($env.EMAIL_RETENCAO_DIAS|to_int) : 180)
    }

    var $dias_desligado {
      value = ($env.DESLIGADO_RETENCAO_DIAS != null ? ($env.DESLIGADO_RETENCAO_DIAS|to_int) : 1825)
    }

    // ---------- 1. Desligamentos agendados com data efetiva atingida ----------
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.status == "agendado" && $db.solicitacao_desligamento.data_efetiva != null && $db.solicitacao_desligamento.data_efetiva <= $hoje
      return = {type: "list"}
    } as $desligamentos_vencidos

    // Colaboradores que saem hoje: ficam de fora das transicoes de status.
    var $ids_desligando {
      value = ","
    }

    foreach ($desligamentos_vencidos) {
      each as $solicitacao_item {
        db.get colaborador {
          field_name = "id"
          field_value = $solicitacao_item.colaborador_id
        } as $colaborador_desligando

        conditional {
          if ($colaborador_desligando != null && $colaborador_desligando.status != "Desligado") {
            var.update $ids_desligando {
              value = $ids_desligando ~ ($colaborador_desligando.id|to_text) ~ ","
            }

            var.update $n_desligamentos {
              value = $n_desligamentos + 1
            }

            conditional {
              if ($input.aplicar) {
                db.query historico_profissional {
                  where = $db.historico_profissional.colaborador_id == $colaborador_desligando.id
                  sort = {historico_profissional.data_inicio: "desc"}
                  return = {type: "single"}
                } as $historico_atual

                db.transaction {
                  stack {
                    db.edit solicitacao_desligamento {
                      field_name = "id"
                      field_value = $solicitacao_item.id
                      data = {status: "concluido", data_conclusao: "now", updated_at: "now"}
                    } as $solicitacao_concluida

                    db.edit colaborador {
                      field_name = "id"
                      field_value = $colaborador_desligando.id
                      data = {status: "Desligado", data_desligamento: $solicitacao_item.data_efetiva, updated_at: "now"}
                    } as $colaborador_desligado

                    // Desativa o acesso e revoga todas as sessoes da conta.
                    conditional {
                      if ($colaborador_desligando.user_id != null) {
                        db.edit user {
                          field_name = "id"
                          field_value = $colaborador_desligando.user_id
                          data = {ativo: false, updated_at: "now"}
                        } as $conta_desativada

                        db.query sessao {
                          where = $db.sessao.user_id == $colaborador_desligando.user_id && $db.sessao.ativa == true
                          return = {type: "list"}
                        } as $sessoes_a_revogar

                        foreach ($sessoes_a_revogar) {
                          each as $sessao_revogavel {
                            db.edit sessao {
                              field_name = "id"
                              field_value = $sessao_revogavel.id
                              data = {ativa: false, revogada_em: "now", updated_at: "now"}
                            } as $sessao_revogada
                          }
                        }
                      }
                    }

                    conditional {
                      if ($historico_atual != null && $historico_atual.data_fim == null) {
                        db.edit historico_profissional {
                          field_name = "id"
                          field_value = $historico_atual.id
                          data = {data_fim: $solicitacao_item.data_efetiva, updated_at: "now"}
                        } as $historico_encerrado
                      }
                    }

                    db.add historico_profissional {
                      data = {
                        colaborador_id       : $colaborador_desligando.id
                        cargo_id             : $colaborador_desligando.cargo_id
                        departamento_id      : $colaborador_desligando.departamento_id
                        tipo_contrato        : $colaborador_desligando.tipo_contrato
                        nivel                : $colaborador_desligando.nivel
                        salario              : $colaborador_desligando.salario
                        carga_horaria_semanal: $colaborador_desligando.carga_horaria_semanal
                        data_inicio          : $solicitacao_item.data_efetiva
                        data_fim             : null
                        tipo_alteracao       : "desligamento"
                        motivo_alteracao     : $solicitacao_item.motivo_decisao
                        user_id              : $solicitacao_item.decidido_por_user_id
                        updated_at           : "now"
                      }
                    } as $historico_desligamento

                    db.add auditoria {
                      data = {
                        user_id    : $input.usuario_id
                        acao       : "concluir_desligamento_agendado"
                        recurso    : "solicitacao_desligamento"
                        registro_id: $solicitacao_item.id
                        resultado  : "sucesso"
                      }
                    } as $evento_desligamento
                  }
                }
              }
            }
          }
        }
      }
    }

    // ---------- 2. Ferias aprovadas com data final no passado ----------
    db.query ferias {
      where = $db.ferias.status == "Aprovada" && $db.ferias.data_fim != null && $db.ferias.data_fim < $hoje
      return = {type: "list"}
      output = ["id"]
    } as $ferias_encerradas

    var.update $n_ferias_concluidas {
      value = $ferias_encerradas|count
    }

    conditional {
      if ($input.aplicar) {
        foreach ($ferias_encerradas) {
          each as $ferias_item {
            db.edit ferias {
              field_name = "id"
              field_value = $ferias_item.id
              data = {status: "Concluida", updated_at: "now"}
            } as $ferias_concluida
          }
        }
      }
    }

    // ---------- 3. Ponto aberto de dias anteriores ----------
    db.query registro_ponto {
      where = $db.registro_ponto.status == "Aberto" && $db.registro_ponto.data != null && $db.registro_ponto.data < $hoje
      return = {type: "list"}
      output = ["id"]
    } as $pontos_abertos

    var.update $n_ponto_incompleto {
      value = $pontos_abertos|count
    }

    conditional {
      if ($input.aplicar) {
        foreach ($pontos_abertos) {
          each as $ponto_item {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $ponto_item.id
              data = {status: "Incompleto", updated_at: "now"}
            } as $ponto_incompleto
          }
        }
      }
    }

    // ---------- 4. Instrumentos vigentes com vigencia encerrada ----------
    db.query instrumento_normativo {
      where = $db.instrumento_normativo.status == "vigente" && $db.instrumento_normativo.data_fim != null && $db.instrumento_normativo.data_fim < $hoje
      return = {type: "list"}
      output = ["id"]
    } as $instrumentos_vencidos

    var.update $n_instrumentos_expirados {
      value = $instrumentos_vencidos|count
    }

    conditional {
      if ($input.aplicar) {
        foreach ($instrumentos_vencidos) {
          each as $instrumento_item {
            db.edit instrumento_normativo {
              field_name = "id"
              field_value = $instrumento_item.id
              data = {status: "expirado", updated_at: "now"}
            } as $instrumento_expirado
          }
        }
      }
    }

    // ---------- 5 e 6. Status do colaborador: Ferias e Afastado ----------
    db.query ferias {
      where = $db.ferias.status == "Aprovada" && $db.ferias.data_inicio != null && $db.ferias.data_inicio <= $hoje && $db.ferias.data_fim != null && $db.ferias.data_fim >= $hoje
      return = {type: "list"}
      output = ["id", "colaborador_id"]
    } as $ferias_vigentes

    // Ausencias que cobrem hoje. O filtro por tipo (Afastamento ou Licenca) e por
    // status (Aprovada ou Registrado) e feito no laco, porque um `||` entre
    // parenteses dentro do `where` nao filtrou corretamente neste workspace.
    db.query ausencia {
      where = $db.ausencia.data_inicio != null && $db.ausencia.data_inicio <= $hoje && $db.ausencia.data_fim != null && $db.ausencia.data_fim >= $hoje
      return = {type: "list"}
      output = ["id", "colaborador_id", "tipo", "status"]
    } as $ausencias_de_hoje

    var $afastamentos_vigentes {
      value = []
    }

    foreach ($ausencias_de_hoje) {
      each as $ausencia_de_hoje {
        conditional {
          if (($ausencia_de_hoje.tipo == "Afastamento" || $ausencia_de_hoje.tipo == "Licenca") && ($ausencia_de_hoje.status == "Aprovada" || $ausencia_de_hoje.status == "Registrado")) {
            var.update $afastamentos_vigentes {
              value = $afastamentos_vigentes|push:$ausencia_de_hoje
            }
          }
        }
      }
    }

    var $ids_em_ferias {
      value = ","
    }

    foreach ($ferias_vigentes) {
      each as $ferias_vigente_item {
        var.update $ids_em_ferias {
          value = $ids_em_ferias ~ ($ferias_vigente_item.colaborador_id|to_text) ~ ","
        }
      }
    }

    var $ids_afastados {
      value = ","
    }

    foreach ($afastamentos_vigentes) {
      each as $afastamento_item {
        var.update $ids_afastados {
          value = $ids_afastados ~ ($afastamento_item.colaborador_id|to_text) ~ ","
        }
      }
    }

    // 5a. Ativo com ferias em andamento passa a Ferias.
    foreach ($ferias_vigentes) {
      each as $ferias_vigente_item {
        db.get colaborador {
          field_name = "id"
          field_value = $ferias_vigente_item.colaborador_id
        } as $colaborador_ferias

        conditional {
          if ($colaborador_ferias != null && $colaborador_ferias.status == "Ativo" && ($ids_desligando|contains:("," ~ ($colaborador_ferias.id|to_text) ~ ",")) == false) {
            var.update $n_para_ferias {
              value = $n_para_ferias + 1
            }

            conditional {
              if ($input.aplicar) {
                db.edit colaborador {
                  field_name = "id"
                  field_value = $colaborador_ferias.id
                  data = {status: "Ferias", updated_at: "now"}
                } as $colaborador_em_ferias
              }
            }
          }
        }
      }
    }

    // 5b. Quem esta como Ferias sem ferias em andamento volta a Ativo, ou vai a
    // Afastado se houver afastamento vigente.
    db.query colaborador {
      where = $db.colaborador.status == "Ferias"
      return = {type: "list"}
      output = ["id"]
    } as $colaboradores_em_ferias

    foreach ($colaboradores_em_ferias) {
      each as $colaborador_ferias_item {
        var $chave_ferias {
          value = "," ~ ($colaborador_ferias_item.id|to_text) ~ ","
        }

        conditional {
          if (($ids_em_ferias|contains:$chave_ferias) == false && ($ids_desligando|contains:$chave_ferias) == false) {
            conditional {
              if ($ids_afastados|contains:$chave_ferias) {
                var.update $n_para_afastado {
                  value = $n_para_afastado + 1
                }

                conditional {
                  if ($input.aplicar) {
                    db.edit colaborador {
                      field_name = "id"
                      field_value = $colaborador_ferias_item.id
                      data = {status: "Afastado", updated_at: "now"}
                    } as $colaborador_afastado_5b
                  }
                }
              }

              else {
                var.update $n_para_ativo {
                  value = $n_para_ativo + 1
                }

                conditional {
                  if ($input.aplicar) {
                    db.edit colaborador {
                      field_name = "id"
                      field_value = $colaborador_ferias_item.id
                      data = {status: "Ativo", updated_at: "now"}
                    } as $colaborador_ativo_5b
                  }
                }
              }
            }
          }
        }
      }
    }

    // 6a. Ativo com afastamento em andamento (e sem ferias em andamento) passa a Afastado.
    foreach ($afastamentos_vigentes) {
      each as $afastamento_item {
        db.get colaborador {
          field_name = "id"
          field_value = $afastamento_item.colaborador_id
        } as $colaborador_afastamento

        conditional {
          if ($colaborador_afastamento != null && $colaborador_afastamento.status == "Ativo" && ($ids_em_ferias|contains:("," ~ ($colaborador_afastamento.id|to_text) ~ ",")) == false && ($ids_desligando|contains:("," ~ ($colaborador_afastamento.id|to_text) ~ ",")) == false) {
            var.update $n_para_afastado {
              value = $n_para_afastado + 1
            }

            conditional {
              if ($input.aplicar) {
                db.edit colaborador {
                  field_name = "id"
                  field_value = $colaborador_afastamento.id
                  data = {status: "Afastado", updated_at: "now"}
                } as $colaborador_afastado
              }
            }
          }
        }
      }
    }

    // 6b. Quem esta como Afastado sem afastamento em andamento volta a Ativo, ou vai a
    // Ferias se houver ferias em andamento.
    db.query colaborador {
      where = $db.colaborador.status == "Afastado"
      return = {type: "list"}
      output = ["id"]
    } as $colaboradores_afastados

    foreach ($colaboradores_afastados) {
      each as $colaborador_afastado_item {
        var $chave_afastado {
          value = "," ~ ($colaborador_afastado_item.id|to_text) ~ ","
        }

        conditional {
          if (($ids_afastados|contains:$chave_afastado) == false && ($ids_desligando|contains:$chave_afastado) == false) {
            conditional {
              if ($ids_em_ferias|contains:$chave_afastado) {
                var.update $n_para_ferias {
                  value = $n_para_ferias + 1
                }

                conditional {
                  if ($input.aplicar) {
                    db.edit colaborador {
                      field_name = "id"
                      field_value = $colaborador_afastado_item.id
                      data = {status: "Ferias", updated_at: "now"}
                    } as $colaborador_ferias_6b
                  }
                }
              }

              else {
                var.update $n_para_ativo {
                  value = $n_para_ativo + 1
                }

                conditional {
                  if ($input.aplicar) {
                    db.edit colaborador {
                      field_name = "id"
                      field_value = $colaborador_afastado_item.id
                      data = {status: "Ativo", updated_at: "now"}
                    } as $colaborador_ativo_6b
                  }
                }
              }
            }
          }
        }
      }
    }

    // ---------- 7. Retencao: IP e dispositivo de sessoes antigas ----------
    // Sessao encerrada ou expirada ha mais que o prazo perde `endereco_ip` e
    // `dispositivo`. A sessao em si fica (so deixa de identificar o aparelho).
    var $segundos_sessao {
      value = $dias_sessao * 86400
    }

    var $corte_sessao {
      value = now|add_secs_to_timestamp:(0 - $segundos_sessao)
    }

    db.query sessao {
      where = $db.sessao.expira_em < $corte_sessao
      return = {type: "list"}
      output = ["id", "endereco_ip", "dispositivo"]
    } as $sessoes_antigas

    foreach ($sessoes_antigas) {
      each as $sessao_antiga {
        conditional {
          if ($sessao_antiga.endereco_ip != null || $sessao_antiga.dispositivo != null) {
            var.update $n_sessoes_limpas {
              value = $n_sessoes_limpas + 1
            }

            conditional {
              if ($input.aplicar) {
                db.edit sessao {
                  field_name = "id"
                  field_value = $sessao_antiga.id
                  data = {endereco_ip: null, dispositivo: null, updated_at: "now"}
                } as $sessao_limpa
              }
            }
          }
        }
      }
    }

    // ---------- 8. Retencao: e-mails ja enviados ha mais que o prazo ----------
    // Destinatario e corpo viram marcadores; a linha (e a chave de idempotencia) fica.
    var $segundos_email {
      value = $dias_email * 86400
    }

    var $corte_email {
      value = now|add_secs_to_timestamp:(0 - $segundos_email)
    }

    db.query email_outbox {
      where = $db.email_outbox.status == "enviado" && $db.email_outbox.enviado_em != null && $db.email_outbox.enviado_em < $corte_email && $db.email_outbox.destinatario_email != "removido@anonimizado.invalid"
      return = {type: "list"}
      output = ["id"]
    } as $emails_antigos

    var.update $n_emails_limpos {
      value = $emails_antigos|count
    }

    conditional {
      if ($input.aplicar) {
        foreach ($emails_antigos) {
          each as $email_antigo {
            db.edit email_outbox {
              field_name = "id"
              field_value = $email_antigo.id
              data = {destinatario_email: "removido@anonimizado.invalid", destinatario_nome: null, corpo: "[conteudo removido por prazo de retencao]", updated_at: "now"}
            } as $email_limpo
          }
        }
      }
    }

    // ---------- 9. Retencao: desligados com prazo de guarda cumprido (so lista) ----------
    // Nada e alterado aqui: a anonimizacao e uma decisao do RH, feita em
    // `colaboradores/{id}/anonimizar`. Esta lista so avisa quem ja pode ser anonimizado.
    var $segundos_desligado {
      value = $dias_desligado * 86400
    }

    var $corte_desligado {
      value = now|add_secs_to_timestamp:(0 - $segundos_desligado)|format_timestamp:"Y-m-d":"UTC"
    }

    db.query colaborador {
      where = $db.colaborador.status == "Desligado" && $db.colaborador.data_desligamento != null && $db.colaborador.data_desligamento <= $corte_desligado && $db.colaborador.anonimizado_em == null
      sort = {colaborador.data_desligamento: "asc"}
      return = {type: "list"}
      output = ["id", "data_desligamento"]
    } as $desligados_prazo_cumprido

    var $contagens {
      value = {
        desligamentos_concluidos: $n_desligamentos
        ferias_concluidas       : $n_ferias_concluidas
        ponto_para_incompleto   : $n_ponto_incompleto
        instrumentos_expirados  : $n_instrumentos_expirados
        colaboradores_para_ferias  : $n_para_ferias
        colaboradores_para_afastado: $n_para_afastado
        colaboradores_para_ativo   : $n_para_ativo
        sessoes_ip_dispositivo_limpos: $n_sessoes_limpas
        emails_enviados_limpos     : $n_emails_limpos
        desligados_prazo_cumprido  : $desligados_prazo_cumprido
      }
    }
  }

  response = $contagens

  tags = ["conectahr"]
  guid = "conectahr-processar-transicoes-diarias-0001"
}
