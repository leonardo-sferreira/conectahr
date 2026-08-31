// Lista as solicitacoes de correcao de ponto do colaborador autenticado.
query "minhas_correcoes_ponto" verb=GET {
  api_group = "ConectaRH - Ponto"
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

    db.query correcao_ponto {
      where = $db.correcao_ponto.colaborador_id == $colaborador_autenticado.id
      sort = {correcao_ponto.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_correcoes
  }

  response = {
    sucesso   : true
    correcoes : $minhas_correcoes
  }

  guid = "conectahr-minhas-correcoes-ponto-get-0001"
}
