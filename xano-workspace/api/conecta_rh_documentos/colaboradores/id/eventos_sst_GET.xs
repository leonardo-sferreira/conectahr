// Consulta os eventos de SST de um colaborador. Acesso restrito:
// RH/ADMIN, ou o proprio colaborador. Gestor NAO tem acesso (mesmo
// modelo ja usado para documentos em geral, item 5.9).
query "colaboradores/{id}/eventos_sst" verb=GET {
  api_group = "ConectaRH - Documentos"
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

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo.user_id == $usuario_autenticado.id)
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar estes eventos de SST."
    }

    db.query evento_sst {
      where = $db.evento_sst.colaborador_id == $colaborador_alvo.id
      sort = {evento_sst.data_exame: "desc"}
      return = {type: "list"}
    } as $eventos
  }

  response = {
    sucesso: true
    eventos: $eventos
  }

  guid = "conectahr-colaboradores-eventos-sst-get-0001"
}
