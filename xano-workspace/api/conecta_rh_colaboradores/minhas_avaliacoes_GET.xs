// Lista as avaliacoes que o usuario autenticado precisa responder
// (onde ele e o avaliador).
query "minhas_avaliacoes" verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    db.query avaliacao {
      where = $db.avaliacao.user_id == $usuario_autenticado.id
      sort = {avaliacao.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_avaliacoes
  }

  response = {
    sucesso     : true
    avaliacoes  : $minhas_avaliacoes
  }

  guid = "conectahr-minhas-avaliacoes-get-0001"
}
