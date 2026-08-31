// Colaborador responde a uma pergunta de clima. A resposta e gravada
// sem nenhuma identidade (nem colaborador_id, nem user_id) - so o
// departamento atual do colaborador, para permitir agrupamento. Um
// registro separado (`resposta_clima_participacao`) bloqueia responder
// a mesma pergunta duas vezes, sem nunca ser cruzado com a nota em si.
query "perguntas_clima/{id}/responder" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int nota
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

    db.get pergunta_clima {
      field_name = "id"
      field_value = $input.id
    } as $pergunta

    precondition ($pergunta != null) {
      error_type = "notfound"
      error = "Pergunta nao encontrada."
    }

    precondition ($input.nota >= 1 && $input.nota <= 5) {
      error_type = "inputerror"
      error = "A nota deve estar entre 1 e 5."
    }

    // Bloqueia responder a mesma pergunta duas vezes.
    db.query resposta_clima_participacao {
      where = $db.resposta_clima_participacao.pergunta_clima_id == $pergunta.id && $db.resposta_clima_participacao.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $participacao_existente

    precondition ($participacao_existente == null) {
      error_type = "inputerror"
      error = "Voce ja respondeu esta pergunta."
    }

    db.transaction {
      stack {
        db.add resposta_clima {
          data = {
            pergunta_clima_id: $pergunta.id
            departamento_id  : $colaborador_autenticado.departamento_id
            nota             : $input.nota
          }
        } as $resposta_criada

        db.add resposta_clima_participacao {
          data = {
            pergunta_clima_id: $pergunta.id
            colaborador_id   : $colaborador_autenticado.id
          }
        } as $participacao_criada
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Resposta registrada com sucesso."
  }

  guid = "conectahr-perguntas-clima-responder-post-0001"
}
