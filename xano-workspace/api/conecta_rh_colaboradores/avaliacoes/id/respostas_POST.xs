// O avaliador registra (ou atualiza) a nota de uma competencia dentro
// de uma avaliacao atribuida a ele. Pode ser chamado uma vez por
// competencia; chamar de novo para a mesma competencia atualiza a
// resposta em vez de duplicar. Move a avaliacao para em_andamento na
// primeira resposta.
query "avaliacoes/{id}/respostas" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int competencia_avaliacao_id
    int nota
    text? comentario? filters=trim|max:2000
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

    db.get avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $avaliacao_atual

    precondition ($avaliacao_atual != null) {
      error_type = "notfound"
      error = "Avaliacao nao encontrada."
    }

    precondition ($avaliacao_atual.user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Somente o avaliador designado pode responder esta avaliacao."
    }

    precondition ($avaliacao_atual.status == "pendente" || $avaliacao_atual.status == "em_andamento") {
      error_type = "inputerror"
      error = "Esta avaliacao ja foi enviada ou cancelada."
    }

    db.get competencia_avaliacao {
      field_name = "id"
      field_value = $input.competencia_avaliacao_id
    } as $competencia

    precondition ($competencia != null) {
      error_type = "notfound"
      error = "Competencia nao encontrada."
    }

    precondition ($input.nota >= 1 && $input.nota <= 5) {
      error_type = "inputerror"
      error = "A nota deve estar entre 1 e 5."
    }

    db.query resposta_avaliacao {
      where = $db.resposta_avaliacao.avaliacao_id == $avaliacao_atual.id && $db.resposta_avaliacao.competencia_avaliacao_id == $competencia.id
      return = {type: "single"}
    } as $resposta_existente

    conditional {
      if ($resposta_existente == null) {
        db.add resposta_avaliacao {
          data = {
            avaliacao_id              : $avaliacao_atual.id
            competencia_avaliacao_id  : $competencia.id
            nota                        : $input.nota
            comentario                    : $input.comentario
            updated_at                       : "now"
          }
        } as $resposta_criada
      }
    }

    conditional {
      if ($resposta_existente != null) {
        db.edit resposta_avaliacao {
          field_name = "id"
          field_value = $resposta_existente.id
          data = {nota: $input.nota, comentario: $input.comentario, updated_at: "now"}
        } as $resposta_criada
      }
    }

    // Move a avaliacao para em_andamento na primeira resposta.
    conditional {
      if ($avaliacao_atual.status == "pendente") {
        db.edit avaliacao {
          field_name = "id"
          field_value = $avaliacao_atual.id
          data = {status: "em_andamento", updated_at: "now"}
        } as $avaliacao_atualizada
      }
    }

    // Auditoria: registro de resposta de avaliacao (item 7.11).
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "registrar_resposta_avaliacao"
        recurso    : "resposta_avaliacao"
        registro_id: $resposta_criada.id
        valor_novo : ("competencia_id=" ~ ($competencia.id|to_text) ~ "; nota=" ~ ($input.nota|to_text))
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Resposta registrada com sucesso."
    resposta : $resposta_criada
  }

  guid = "conectahr-avaliacoes-respostas-post-0001"
}
