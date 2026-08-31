// Rotina diaria (ConectaHR). Conclui desligamentos com aviso previo cuja
// data_efetiva ja chegou: encerra o vinculo do colaborador, desativa o
// acesso, registra o evento no historico profissional e fecha a
// solicitacao. Idempotente por natureza: uma vez concluida, a solicitacao
// sai do filtro status == "agendado" e nao e reprocessada em execucoes
// futuras. Espelha o mesmo par status+data que a tarefa equivalente de
// vencimento de documentos (item 5.3) deve seguir.
task concluir_desligamentos_agendados {
  active = true

  stack {
    // Localiza desligamentos agendados cuja data efetiva ja chegou.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.status == "agendado" && $db.solicitacao_desligamento.data_efetiva <= "now"
      return = {type: "list"}
    } as $solicitacoes_vencidas

    foreach ($solicitacoes_vencidas) {
      each as $solicitacao_item {
        db.get colaborador {
          field_name = "id"
          field_value = $solicitacao_item.colaborador_id
        } as $colaborador_item

        // So processa quando o colaborador ainda existe e continua ativo
        // (evita reativar ou duplicar um desligamento ja concluido de
        // outra forma).
        conditional {
          if ($colaborador_item != null && $colaborador_item.status == "Ativo") {
            db.get user {
              field_name = "id"
              field_value = $colaborador_item.user_id
            } as $conta_item

            db.query historico_profissional {
              where = $db.historico_profissional.colaborador_id == $colaborador_item.id
              sort = {historico_profissional.data_inicio: "desc"}
              return = {type: "single"}
            } as $historico_item

            db.transaction {
              stack {
                // Conclui a solicitacao.
                db.edit solicitacao_desligamento {
                  field_name = "id"
                  field_value = $solicitacao_item.id
                  data = {
                    status        : "concluido"
                    data_conclusao: "now"
                    updated_at    : "now"
                  }
                } as $solicitacao_concluida

                // Encerra o vinculo profissional.
                db.edit colaborador {
                  field_name = "id"
                  field_value = $colaborador_item.id
                  data = {
                    status           : "Desligado"
                    data_desligamento: $solicitacao_item.data_efetiva
                    updated_at       : "now"
                  }
                } as $colaborador_desligado

                // Desativa somente o acesso ao ConectaRH.
                conditional {
                  if ($conta_item != null) {
                    db.edit user {
                      field_name = "id"
                      field_value = $conta_item.id
                      data = {ativo: false, updated_at: "now"}
                    } as $conta_desativada
                  }
                }

                // Encerra o historico profissional aberto, se existir.
                conditional {
                  if ($historico_item != null) {
                    conditional {
                      if ($historico_item.data_fim == null) {
                        db.edit historico_profissional {
                          field_name = "id"
                          field_value = $historico_item.id
                          data = {data_fim: $solicitacao_item.data_efetiva, updated_at: "now"}
                        } as $historico_encerrado
                      }
                    }
                  }
                }

                // Registra o desligamento no historico profissional.
                db.add historico_profissional {
                  data = {
                    colaborador_id       : $colaborador_item.id
                    cargo_id              : $colaborador_item.cargo_id
                    departamento_id       : $colaborador_item.departamento_id
                    tipo_contrato         : $colaborador_item.tipo_contrato
                    nivel                 : $colaborador_item.nivel
                    salario               : $colaborador_item.salario
                    carga_horaria_semanal : $colaborador_item.carga_horaria_semanal
                    data_inicio           : $solicitacao_item.data_efetiva
                    data_fim              : null
                    tipo_alteracao        : "desligamento"
                    motivo_alteracao      : $solicitacao_item.motivo_decisao
                    user_id               : $solicitacao_item.decidido_por_user_id
                    updated_at            : "now"
                  }
                } as $historico_desligamento
              }
            }
          }
        }
      }
    }
  }

  schedule = [{
    starts_on: 2026-08-30 03:00:00+0000
    freq     : 86400
  }]

  tags = ["conectahr", "desligamento"]
  guid = "conectahr-concluir-desligamentos-agendados-0001"
}
