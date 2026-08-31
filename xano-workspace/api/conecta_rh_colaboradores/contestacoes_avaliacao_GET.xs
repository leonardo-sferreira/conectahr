// RH/ADMIN lista contestacoes de avaliacao em aberto, para revisao humana.
query "contestacoes_avaliacao" verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar contestacoes."
    }

    db.query contestacao_avaliacao {
      where = $db.contestacao_avaliacao.status == "aberta"
      sort = {contestacao_avaliacao.created_at: "asc"}
      return = {type: "list"}
    } as $contestacoes
  }

  response = {
    sucesso       : true
    contestacoes  : $contestacoes
  }

  guid = "conectahr-contestacoes-avaliacao-get-0001"
}
