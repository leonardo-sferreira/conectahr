// Lista as acoes de PDI do colaborador autenticado.
query "meu_pdi" verb=GET {
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

    db.query pdi {
      where = $db.pdi.colaborador_id == $colaborador_autenticado.id
      sort = {pdi.created_at: "desc"}
      return = {type: "list"}
    } as $meu_pdi
  }

  response = {
    sucesso: true
    pdi    : $meu_pdi
  }

  guid = "conectahr-meu-pdi-get-0001"
}
