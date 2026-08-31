// Lista as delegacoes do usuario autenticado, como titular ou substituto.
query "minhas_delegacoes" verb=GET {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
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

    db.query delegacao_aprovacao {
      where = $db.delegacao_aprovacao.titular_user_id == $usuario_autenticado.id || $db.delegacao_aprovacao.substituto_user_id == $usuario_autenticado.id
      sort = {delegacao_aprovacao.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_delegacoes
  }

  response = {
    sucesso     : true
    delegacoes  : $minhas_delegacoes
  }

  guid = "conectahr-minhas-delegacoes-get-0001"
}
