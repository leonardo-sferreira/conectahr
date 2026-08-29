// Cancela uma solicitação de desligamento.
// Somente o usuário que criou a solicitação pode cancelar.
// O cancelamento é permitido apenas enquanto estiver pendente.
query "solicitacoes_desligamento/{id}/cancelar" verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
    text motivo_cancelamento filters=trim|min:5|max:1000
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
  
    // Contas inativas não podem cancelar solicitações.
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
  
    // Apenas Colaborador ou Gestor podem cancelar
    // as próprias solicitações.
    precondition ($perfil_autenticado == "COLABORADOR" || $perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente colaboradores ou gestores podem cancelar solicitações próprias."
    }
  
    // Confirma que existe um colaborador vinculado.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Não existe um colaborador vinculado à conta autenticada."
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
  
    // Somente quem criou a solicitação pode cancelá-la.
    precondition ($solicitacao.solicitante_user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Somente o usuário que criou a solicitação pode cancelá-la."
    }
  
    // Normaliza o status atual.
    var $status_atual {
      value = $solicitacao.status|trim|to_lower
    }
  
    // Só é possível cancelar enquanto estiver pendente.
    precondition ($status_atual == "pendente") {
      error_type = "inputerror"
      error = "Somente solicitações pendentes podem ser canceladas."
    }
  
    // Atualiza a solicitação sem excluir o registro.
    db.edit solicitacao_desligamento {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        status               : "cancelada"
        motivo_cancelamento  : $input.motivo_cancelamento
        cancelado_por_user_id: $usuario_autenticado.id
        data_cancelamento    : "now"
        updated_at           : "now"
      }
    } as $solicitacao_cancelada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitação de desligamento cancelada com sucesso."
    solicitacao: $solicitacao_cancelada
  }

  guid = "93_8ILy3t4J2bgnwIq6g1ywpREk"
}