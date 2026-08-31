// Lista instrumentos normativos, mais recentes primeiro.
query instrumentos_normativos verb=GET {
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

    db.query instrumento_normativo {
      sort = {instrumento_normativo.created_at: "desc"}
      return = {type: "list"}
    } as $instrumentos
  }

  response = {
    sucesso     : true
    instrumentos: $instrumentos
  }

  guid = "conectahr-instrumentos-normativos-get-0001"
}
