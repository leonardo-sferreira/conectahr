// RH/ADMIN cria uma pesquisa de clima. As perguntas sao adicionadas
// separadamente via `pesquisas_clima/{id}/perguntas`.
query pesquisas_clima verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text titulo filters=trim|max:200
    text? descricao? filters=trim|max:1000
    date data_inicio
    date data_fim
    int? minimo_respostas? filters=min:2
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
      error = "Somente RH ou ADMIN podem criar pesquisas de clima."
    }

    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim nao pode ser anterior a data de inicio."
    }

    var $minimo_final {
      value = ($input.minimo_respostas != null ? $input.minimo_respostas : 5)
    }

    db.add pesquisa_clima {
      data = {
        titulo             : $input.titulo
        descricao             : $input.descricao
        data_inicio              : $input.data_inicio
        data_fim                    : $input.data_fim
        minimo_respostas               : $minimo_final
        criado_por_user_id                : $usuario_autenticado.id
        ativo                                : true
        updated_at                              : "now"
      }
    } as $pesquisa_criada
  }

  response = {
    sucesso : true
    mensagem: "Pesquisa de clima criada com sucesso."
    pesquisa: $pesquisa_criada
  }

  guid = "conectahr-pesquisas-clima-post-0001"
}
