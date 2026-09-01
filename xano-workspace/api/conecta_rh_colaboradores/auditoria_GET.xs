// Consulta a trilha de auditoria (item 7.11). Exclusivo de RH/ADMIN.
// Todos os filtros sao opcionais; sem filtro nenhum, retorna os eventos
// mais recentes primeiro. Nunca expoe senha, token ou codigo de acesso —
// os proprios eventos de auditoria ja sao gravados sem esses valores em
// nenhum campo (registrar_evento_sensivel/db.add auditoria em todo o
// codebase grava so acao/recurso/registro_id/valores/justificativa/
// resultado, nunca segredos).
query auditoria verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text? recurso? filters=trim
    int? registro_id?
    int? user_id?
    text? acao? filters=trim
    text? resultado? filters=trim
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
      error = "Somente RH ou ADMIN podem consultar a trilha de auditoria."
    }

    db.query auditoria {
      where = ($input.recurso == null || $db.auditoria.recurso == $input.recurso) && ($input.registro_id == null || $db.auditoria.registro_id == $input.registro_id) && ($input.user_id == null || $db.auditoria.user_id == $input.user_id) && ($input.acao == null || $db.auditoria.acao == $input.acao) && ($input.resultado == null || $db.auditoria.resultado == $input.resultado)
      sort = {auditoria.created_at: "desc"}
      return = {type: "list"}
    } as $eventos
  }

  response = {
    sucesso : true
    total   : ($eventos|count)
    eventos : $eventos
  }

  guid = "conectahr-auditoria-get-0001"
}
