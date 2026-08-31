// Lista os ciclos de avaliacao ativos, mais recentes primeiro.
query ciclos_avaliacao verb=GET {
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

    db.query ciclo_avaliacao {
      where = $db.ciclo_avaliacao.ativo == true
      sort = {ciclo_avaliacao.created_at: "desc"}
      return = {type: "list"}
    } as $ciclos
  }

  response = {
    sucesso: true
    ciclos : $ciclos
  }

  guid = "conectahr-ciclos-avaliacao-get-0001"
}
