// RH/ADMIN adiciona uma pergunta a uma pesquisa de clima ativa.
query "pesquisas_clima/{id}/perguntas" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text texto filters=trim|max:500
    int? ordem?
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem adicionar perguntas."
    }

    db.get pesquisa_clima {
      field_name = "id"
      field_value = $input.id
    } as $pesquisa

    precondition ($pesquisa != null) {
      error_type = "notfound"
      error = "Pesquisa de clima nao encontrada."
    }

    // "!= null" trata 0 como igual a null nesta plataforma (ver
    // conectahr-xano-platform-quirks) — comparar como texto preserva a
    // distincao entre "ordem 0" (valida) e "nao informado".
    var $ordem_texto {
      value = ($input.ordem|to_text)
    }

    var $ordem_final {
      value = ($ordem_texto != "" ? $input.ordem : 1)
    }

    db.add pergunta_clima {
      data = {
        pesquisa_clima_id: $pesquisa.id
        texto            : $input.texto
        ordem            : $ordem_final
      }
    } as $pergunta_criada
  }

  response = {
    sucesso : true
    mensagem: "Pergunta adicionada com sucesso."
    pergunta: $pergunta_criada
  }

  guid = "conectahr-pesquisas-clima-perguntas-post-0001"
}
