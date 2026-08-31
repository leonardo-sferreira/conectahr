// Lista as metas do colaborador autenticado.
query "minhas_metas" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.query meta_avaliacao {
      where = $db.meta_avaliacao.colaborador_id == $colaborador_autenticado.id
      sort = {meta_avaliacao.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_metas
  }

  response = {
    sucesso: true
    metas  : $minhas_metas
  }

  guid = "conectahr-minhas-metas-get-0001"
}
