// RH/ADMIN listam todas as solicitacoes ao RH, mais recentes primeiro.
query solicitacoes verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar todas as solicitacoes."
    }

    db.query solicitacao_rh {
      sort = {solicitacao_rh.created_at: "desc"}
      return = {type: "list"}
    } as $solicitacoes
  }

  response = {
    sucesso     : true
    solicitacoes: $solicitacoes
  }

  guid = "conectahr-solicitacoes-get-0001"
}
