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
  
    // Contas inativas não podem consultar solicitações.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
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
    precondition ($status_normalizado == "pendente" || $status_normalizado == "aprovado" || $status_normalizado == "rejeitado" || $status_normalizado == "cancelado" || $status_normalizado == "agendado" || $status_normalizado == "concluido") {
      error_type = "inputerror"
      error = "Status inválido. Use pendente, aprovado, rejeitado, cancelado, agendado ou concluido."
    }
  
    // Consulta as solicitações do status informado.
    // As mais antigas aparecem primeiro.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.status == $status_normalizado
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