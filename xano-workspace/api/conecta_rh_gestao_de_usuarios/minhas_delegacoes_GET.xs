// Lista as delegacoes do usuario autenticado, como titular ou substituto.
query "minhas_delegacoes" verb=GET {
  api_group = "ConectaRH — Gestão de Usuários"
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    db.query delegacao_aprovacao {
      where = $db.delegacao_aprovacao.titular_user_id == $usuario_autenticado.id || $db.delegacao_aprovacao.substituto_user_id == $usuario_autenticado.id
      sort = {delegacao_aprovacao.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_delegacoes
  }

  response = {
    sucesso     : true
    delegacoes  : $minhas_delegacoes
  }

  guid = "conectahr-minhas-delegacoes-get-0001"
}
