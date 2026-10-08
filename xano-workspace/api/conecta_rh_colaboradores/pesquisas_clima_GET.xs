// Lista pesquisas de clima ativas e dentro da vigencia, com suas
// perguntas, para o colaborador responder.
query pesquisas_clima verb=GET {
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    db.query pesquisa_clima {
      where = $db.pesquisa_clima.ativo == true && $db.pesquisa_clima.data_inicio <= $hoje && $db.pesquisa_clima.data_fim >= $hoje
      sort = {pesquisa_clima.created_at: "desc"}
      return = {type: "list"}
    } as $pesquisas

    db.query pergunta_clima {
      return = {type: "list"}
    } as $todas_perguntas
  }

  response = {
    sucesso   : true
    pesquisas : $pesquisas
    perguntas : $todas_perguntas
  }

  guid = "conectahr-pesquisas-clima-get-0001"
}
