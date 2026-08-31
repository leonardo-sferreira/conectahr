// Lista os reconhecimentos/feedbacks recebidos pelo colaborador
// autenticado - publicos e privados, pois o destinatario sempre pode
// ver o que recebeu. Isolamento do privado: so o destinatario, o
// remetente e RH/ADMIN veem um registro privado (garantido aqui e em
// `mural_reconhecimento`, que nunca lista privados).
query "meus_reconhecimentos_recebidos" verb=GET {
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

    db.query reconhecimento {
      where = $db.reconhecimento.destinatario_colaborador_id == $colaborador_autenticado.id && $db.reconhecimento.status != "cancelado"
      sort = {reconhecimento.created_at: "desc"}
      return = {type: "list"}
    } as $recebidos
  }

  response = {
    sucesso  : true
    recebidos: $recebidos
  }

  guid = "conectahr-meus-reconhecimentos-recebidos-get-0001"
}
