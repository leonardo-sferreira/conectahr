// Aprova uma solicitação de desligamento.
// Operação exclusiva do RH.
// Imediato: conclui e desativa o acesso agora.
// Aviso prévio: agenda para a data efetiva.
query "solicitacoes_desligamento/{id}/aprovar" verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
    date data_efetiva
    text motivo_decisao filters=trim|min:5|max:1000
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
  
    // Contas inativas não podem aprovar solicitações.
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // A aprovação é exclusiva do RH.
    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode aprovar solicitações de desligamento."
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
  
    // Somente solicitações em análise podem ser aprovadas.
    var $status_solicitacao {
      value = $solicitacao.status|trim|to_lower
    }
  
    precondition ($status_solicitacao == "em_analise") {
      error_type = "inputerror"
      error = "Somente solicitações em análise podem ser aprovadas."
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
  
    // O colaborador precisa estar ativo.
    var $status_colaborador {
      value = $colaborador_alvo.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "inputerror"
      error = "O colaborador relacionado não está ativo."
    }
  
    // Localiza a conta de acesso vinculada.
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
  
    // Normaliza o tipo da solicitação.
    var $tipo_desligamento {
      value = $solicitacao.tipo_desligamento|trim|to_lower
    }
  
    precondition ($tipo_desligamento == "imediato" || $tipo_desligamento == "aviso_previo") {
      error_type = "inputerror"
      error = "O tipo de desligamento da solicitação é inválido."
    }
  
    // Desligamento imediato.
    conditional {
      if ($tipo_desligamento == "imediato") {
        db.transaction {
          stack {
            // Conclui a solicitação.
            db.edit solicitacao_desligamento {
              field_name = "id"
              field_value = $solicitacao.id
              data = {
                status              : "concluido"
                data_efetiva        : $input.data_efetiva
                decidido_por_user_id: $usuario_rh.id
                data_decisao        : "now"
                motivo_decisao      : $input.motivo_decisao
                data_conclusao      : "now"
                updated_at          : "now"
              }
            } as $solicitacao_concluida
          
            // Encerra o vínculo profissional.
            db.edit colaborador {
              field_name = "id"
              field_value = $colaborador_alvo.id
              data = {
                status           : "Desligado"
                data_desligamento: $input.data_efetiva
                updated_at       : "now"
              }
            } as $colaborador_desligado
          
            // Desativa somente o acesso ao ConectaRH.
            db.edit user {
              field_name = "id"
              field_value = $conta_colaborador.id
              data = {ativo: false, updated_at: "now"}
            } as $conta_desativada
          }
        }
      }
    
      // Desligamento com aviso prévio.
      else {
        db.transaction {
          stack {
            // Agenda a conclusão para a data efetiva.
            db.edit solicitacao_desligamento {
              field_name = "id"
              field_value = $solicitacao.id
              data = {
                status              : "agendado"
                data_efetiva        : $input.data_efetiva
                decidido_por_user_id: $usuario_rh.id
                data_decisao        : "now"
                motivo_decisao      : $input.motivo_decisao
                updated_at          : "now"
              }
            } as $solicitacao_agendada
          }
        }
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
  
    db.get user {
      field_name = "id"
      field_value = $conta_colaborador.id
      output = ["id", "nome", "email", "perfil", "ativo"]
    } as $conta_atualizada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitação de desligamento aprovada com sucesso."
    solicitacao: $solicitacao_atualizada
    colaborador: $colaborador_atualizado
    conta      : $conta_atualizada
  }

  guid = "Jje7p1oVZPOqx9CCIvRQylGIp7E"
}