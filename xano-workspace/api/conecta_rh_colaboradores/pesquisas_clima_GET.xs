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
