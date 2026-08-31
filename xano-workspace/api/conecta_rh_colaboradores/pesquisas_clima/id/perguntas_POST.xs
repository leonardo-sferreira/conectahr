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
