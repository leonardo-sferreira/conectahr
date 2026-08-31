// Lista as pendencias de documento do colaborador autenticado.
query "minhas_pendencias_documento" verb=GET {
  api_group = "ConectaRH - Documentos"
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

    db.query pendencia_documento {
      where = $db.pendencia_documento.colaborador_id == $colaborador_autenticado.id
      sort = {pendencia_documento.created_at: "desc"}
      return = {type: "list"}
    } as $pendencias
  }

  response = {
    sucesso    : true
    pendencias : $pendencias
  }

  guid = "conectahr-minhas-pendencias-documento-get-0001"
}
