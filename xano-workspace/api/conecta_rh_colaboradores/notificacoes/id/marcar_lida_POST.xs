// Marca uma notificacao interna como lida (item 5.11). So o proprio
// destinatario pode marcar sua notificacao.
query "notificacoes/{id}/marcar_lida" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    db.get notificacao_interna {
      field_name = "id"
      field_value = $input.id
    } as $notificacao_atual

    // Autorizacao checada antes de qualquer estado da notificacao, para
    // nao revelar existencia/estado de notificacao de outra pessoa.
    precondition ($notificacao_atual != null && $notificacao_atual.destinatario_user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para marcar esta notificacao como lida."
    }

    db.edit notificacao_interna {
      field_name = "id"
      field_value = $notificacao_atual.id
      data = {lida: true, lida_em: "now"}
    } as $notificacao_atualizada
  }

  response = {
    sucesso     : true
    notificacao : $notificacao_atualizada
  }

  guid = "conectahr-notificacoes-marcar-lida-post-0001"
}
