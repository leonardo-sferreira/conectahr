// Rejeita uma solicitação de desligamento.
// Operação exclusiva do RH.
// A rejeição não altera o colaborador nem sua conta.
query "solicitacoes_desligamento/{id}/rejeitar" verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
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
  
    // Contas inativas não podem rejeitar solicitações.
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Normaliza o perfil.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // A rejeição é exclusiva do RH.
    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode rejeitar solicitações de desligamento."
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
  
    // Confirma que o colaborador relacionado ainda existe.
    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador_alvo
  
    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "O colaborador relacionado à solicitação não foi encontrado."
    }
  
    // Normaliza o status atual.
    var $status_atual {
      value = $solicitacao.status|trim|to_lower
    }
  
    // Apenas solicitações em análise podem ser rejeitadas.
    precondition ($status_atual == "em_analise") {
      error_type = "inputerror"
      error = "Somente solicitações em análise podem ser rejeitadas."
    }
  
    // Registra a decisão sem alterar o colaborador
    // ou sua conta de acesso.
    db.edit solicitacao_desligamento {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        status              : "rejeitada"
        decidido_por_user_id: $usuario_rh.id
        data_decisao        : "now"
        motivo_decisao      : $input.motivo_decisao
        updated_at          : "now"
      }
    } as $solicitacao_rejeitada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitação de desligamento rejeitada com sucesso."
    solicitacao: $solicitacao_rejeitada
  }

  guid = "O3k-3RNMJdiZ3q5bKLSNYhsHFAI"
}