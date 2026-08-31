// Conclui manualmente um desligamento agendado cuja data efetiva ja
// chegou. Solucao temporaria: o plano Xano deste workspace nao inclui
// Background Tasks, entao a rotina diaria automatica equivalente
// (xano-workspace/task/concluir_desligamentos_agendados.xs) esta escrita
// mas nao pode ser publicada ainda. Este endpoint reproduz a mesma
// transacao para permitir que o RH conclua manualmente enquanto o
// upgrade do plano nao acontece; deve ser removido (ou deixado como
// acao manual complementar) quando a tarefa automatica for publicada.
// Operacao exclusiva do RH.
query "solicitacoes_desligamento/{id}/concluir" verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuário RH autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh

    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }

    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }

    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode concluir solicitações de desligamento."
    }

    // Localiza a solicitação.
    db.get solicitacao_desligamento {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao

    precondition ($solicitacao != null) {
      error_type = "notfound"
      error = "Solicitação de desligamento não encontrada."
    }

    // Somente solicitações agendadas podem ser concluídas por aqui.
    var $status_solicitacao {
      value = $solicitacao.status|trim|to_lower
    }

    precondition ($status_solicitacao == "agendado") {
      error_type = "inputerror"
      error = "Somente solicitações agendadas podem ser concluídas."
    }

    // A data efetiva precisa ter chegado. Comparar um `date` diretamente
    // com "now" faz comparacao de texto, nao de data (digitos vem antes
    // de 'n' no ASCII, entao qualquer data "<=" "now" e sempre
    // verdadeiro) — converte ambos os lados para timestamp numerico.
    var $data_efetiva_ts {
      value = ($solicitacao.data_efetiva|to_timestamp)
    }

    var $agora_ts_concluir {
      value = (now|to_timestamp)
    }

    precondition ($data_efetiva_ts <= $agora_ts_concluir) {
      error_type = "inputerror"
      error = "A data efetiva desta solicitação ainda não chegou."
    }

    // Localiza o colaborador relacionado.
    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "O colaborador relacionado à solicitação não foi encontrado."
    }

    var $status_colaborador {
      value = $colaborador_alvo.status|trim|to_upper
    }

    precondition ($status_colaborador == "ATIVO") {
      error_type = "inputerror"
      error = "O colaborador relacionado não está ativo."
    }

    precondition ($colaborador_alvo.user_id != null) {
      error_type = "inputerror"
      error = "O colaborador não possui uma conta de acesso vinculada."
    }

    db.get user {
      field_name = "id"
      field_value = $colaborador_alvo.user_id
    } as $conta_colaborador

    precondition ($conta_colaborador != null) {
      error_type = "notfound"
      error = "A conta de acesso do colaborador não foi encontrada."
    }

    // Localiza o registro de historico profissional mais recente,
    // para encerra-lo na conclusao do desligamento.
    db.query historico_profissional {
      where = $db.historico_profissional.colaborador_id == $colaborador_alvo.id
      sort = {historico_profissional.data_inicio: "desc"}
      return = {type: "single"}
    } as $historico_atual

    db.transaction {
      stack {
        // Conclui a solicitação.
        db.edit solicitacao_desligamento {
          field_name = "id"
          field_value = $solicitacao.id
          data = {
            status        : "concluido"
            data_conclusao: "now"
            updated_at    : "now"
          }
        } as $solicitacao_concluida

        // Encerra o vínculo profissional.
        db.edit colaborador {
          field_name = "id"
          field_value = $colaborador_alvo.id
          data = {
            status           : "Desligado"
            data_desligamento: $solicitacao.data_efetiva
            updated_at       : "now"
          }
        } as $colaborador_desligado

        // Desativa somente o acesso ao ConectaRH.
        db.edit user {
          field_name = "id"
          field_value = $conta_colaborador.id
          data = {ativo: false, updated_at: "now"}
        } as $conta_desativada

        // Encerra o historico profissional aberto, se existir.
        conditional {
          if ($historico_atual != null) {
            conditional {
              if ($historico_atual.data_fim == null) {
                db.edit historico_profissional {
                  field_name = "id"
                  field_value = $historico_atual.id
                  data = {data_fim: $solicitacao.data_efetiva, updated_at: "now"}
                } as $historico_encerrado
              }
            }
          }
        }

        // Registra o desligamento no historico profissional.
        db.add historico_profissional {
          data = {
            colaborador_id       : $colaborador_alvo.id
            cargo_id              : $colaborador_alvo.cargo_id
            departamento_id       : $colaborador_alvo.departamento_id
            tipo_contrato         : $colaborador_alvo.tipo_contrato
            nivel                 : $colaborador_alvo.nivel
            salario               : $colaborador_alvo.salario
            carga_horaria_semanal : $colaborador_alvo.carga_horaria_semanal
            data_inicio           : $solicitacao.data_efetiva
            data_fim              : null
            tipo_alteracao        : "desligamento"
            motivo_alteracao      : $solicitacao.motivo_decisao
            user_id               : $solicitacao.decidido_por_user_id
            updated_at            : "now"
          }
        } as $historico_desligamento

        // Auditoria: conclusao manual do desligamento agendado.
        db.add auditoria {
          data = {
            user_id       : $usuario_rh.id
            acao          : "concluir_desligamento_agendado"
            recurso       : "solicitacao_desligamento"
            registro_id   : $solicitacao.id
            resultado     : "sucesso"
          }
        } as $evento_auditoria
      }
    }

    // Recarrega os dados atualizados para a resposta.
    db.get solicitacao_desligamento {
      field_name = "id"
      field_value = $solicitacao.id
    } as $solicitacao_atualizada

    db.get colaborador {
      field_name = "id"
      field_value = $colaborador_alvo.id
    } as $colaborador_atualizado
  }

  response = {
    sucesso    : true
    mensagem   : "Desligamento concluído manualmente com sucesso."
    solicitacao: $solicitacao_atualizada
    colaborador: $colaborador_atualizado
  }

  guid = "conectahr-solicitacoes-desligamento-concluir-post-0001"
}
