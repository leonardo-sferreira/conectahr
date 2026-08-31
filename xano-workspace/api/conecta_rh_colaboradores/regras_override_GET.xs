// Lista regras de override, mais recentes primeiro.
query regras_override verb=GET {
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

    db.query regra_override {
      sort = {regra_override.created_at: "desc"}
      return = {type: "list"}
    } as $overrides
  }

  response = {
    sucesso  : true
    overrides: $overrides
  }

  guid = "conectahr-regras-override-get-0001"
}
