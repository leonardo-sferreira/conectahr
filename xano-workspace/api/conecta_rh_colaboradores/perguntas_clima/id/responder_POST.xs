// Colaborador responde a uma pergunta de clima. Nao existe registro
// individual da resposta: a nota so incrementa o contador de
// `resposta_clima_agregado` (pergunta x departamento x nota), sem data nem
// id proprio, entao nao ha como cruzar com `resposta_clima_participacao`,
// que so serve para bloquear responder a mesma pergunta duas vezes.
// So aceita pesquisa ativa e dentro do periodo, de colaborador nao desligado.
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    precondition ($colaborador_autenticado.status != "Desligado") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode responder pesquisas."
    }

    db.get pergunta_clima {
      field_name = "id"
      field_value = $input.id
    } as $pergunta

    precondition ($pergunta != null) {
      error_type = "notfound"
      error = "Pergunta nao encontrada."
    }

    db.get pesquisa_clima {
      field_name = "id"
      field_value = $pergunta.pesquisa_clima_id
    } as $pesquisa

    precondition ($pesquisa != null && $pesquisa.ativo) {
      error_type = "inputerror"
      error = "Esta pesquisa nao esta aberta para respostas."
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    precondition ($pesquisa.data_inicio <= $hoje && $pesquisa.data_fim >= $hoje) {
      error_type = "inputerror"
      error = "Esta pesquisa esta fora do periodo de respostas."
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

    // 0 = sem departamento (ver resposta_clima_agregado.xs).
    var $departamento_agregado {
      value = ($colaborador_autenticado.departamento_id == null ? 0 : $colaborador_autenticado.departamento_id)
    }

    db.query resposta_clima_agregado {
      where = $db.resposta_clima_agregado.pergunta_clima_id == $pergunta.id && $db.resposta_clima_agregado.departamento_id == $departamento_agregado && $db.resposta_clima_agregado.nota == $input.nota
      return = {type: "single"}
    } as $contador_existente

    db.transaction {
      stack {
        conditional {
          if ($contador_existente == null) {
            db.add resposta_clima_agregado {
              data = {
                pergunta_clima_id: $pergunta.id
                departamento_id  : $departamento_agregado
                nota             : $input.nota
                quantidade       : 1
              }
            } as $contador_criado
          }

          else {
            db.edit resposta_clima_agregado {
              field_name = "id"
              field_value = $contador_existente.id
              data = {quantidade: $contador_existente.quantidade + 1}
            } as $contador_atualizado
          }
        }

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
