// Inicia a análise de uma solicitação de desligamento.
// Operação exclusiva do RH.
// Apenas solicitações pendentes podem entrar em análise.
query "solicitacoes_desligamento/{id}/iniciar_analise" verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh
  
    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Contas inativas não podem iniciar análises.
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
  
    // A análise é exclusiva do RH.
    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode iniciar a análise de uma solicitação de desligamento."
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
  
    // Apenas solicitações pendentes podem iniciar análise.
    precondition ($status_atual == "pendente") {
      error_type = "inputerror"
      error = "Somente solicitações pendentes podem entrar em análise."
    }
  
    // Altera o status e registra responsável e data de início.
    db.edit solicitacao_desligamento {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        status                : "em_analise"
        responsavel_rh_user_id: $usuario_rh.id
        data_inicio_analise   : "now"
        updated_at            : "now"
      }
    } as $solicitacao_em_analise
  }

  response = {
    sucesso    : true
    mensagem   : "Análise da solicitação de desligamento iniciada com sucesso."
    solicitacao: $solicitacao_em_analise
  }

  guid = "f0rZmSLpDcKiLELxxGnjg6bKEWo"
}