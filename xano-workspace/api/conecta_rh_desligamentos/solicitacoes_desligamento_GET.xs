// Lista as solicitações de desligamento para análise do RH.
// A consulta exige um status e ordena as solicitações
// mais antigas primeiro.
query solicitacoes_desligamento verb=GET {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    text status filters=trim
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }
  
    // Contas inativas não podem consultar solicitações.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // A fila de desligamentos é exclusiva do RH.
    precondition ($perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode consultar solicitações de desligamento."
    }
  
    // Normaliza o status recebido.
    var $status_normalizado {
      value = $input.status|trim|to_lower
    }
  
    // Valida os valores configurados no Enum.
    precondition ($status_normalizado == "pendente" || $status_normalizado == "em_analise" || $status_normalizado == "agendado" || $status_normalizado == "rejeitada" || $status_normalizado == "cancelada" || $status_normalizado == "concluido") {
      error_type = "inputerror"
      error = "Status inválido. Use pendente, em_analise, agendado, rejeitada, cancelada ou concluido."
    }
  
    // Consulta as solicitações do status informado.
    // As mais antigas aparecem primeiro.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.status == $status_normalizado
      sort = {solicitacao_desligamento.created_at: "asc"}
      return = {type: "list"}
    } as $solicitacoes
  
    // Conta quantas solicitações foram localizadas.
    var $quantidade {
      value = $solicitacoes|count
    }
  }

  response = {
    sucesso     : true
    status      : $status_normalizado
    quantidade  : $quantidade
    solicitacoes: $solicitacoes
  }

  guid = "YwwbapGnz7ci80sugRFLhkw55PA"
}