// Lista as pendencias de documento (RH/ADMIN).
query "pendencias_documento" verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar pendencias de documento."
    }

    db.query pendencia_documento {
      sort = {pendencia_documento.created_at: "desc"}
      return = {type: "list"}
    } as $pendencias
  }

  response = {
    sucesso    : true
    pendencias : $pendencias
  }

  guid = "conectahr-pendencias-documento-get-0001"
}
