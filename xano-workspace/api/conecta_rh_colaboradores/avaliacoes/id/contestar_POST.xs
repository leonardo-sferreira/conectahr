// O colaborador avaliado contesta uma avaliacao ja enviada, abrindo
// revisao humana. Nao altera a avaliacao original (Requirement:
// "Avaliacao justa e nao discriminatoria" - "sem alterar retroativamente
// a avaliacao original").
query "avaliacoes/{id}/contestar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text motivo filters=trim|min:5|max:2000
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

    db.get colaborador {
      field_name = "id"
      field_value = $avaliacao_atual.colaborador_id
    } as $colaborador_avaliado

    // Autorizacao checada antes do status da avaliacao, para nao revelar
    // esse status a quem nao e o proprio avaliado.
    precondition ($colaborador_avaliado != null && $colaborador_avaliado.user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Somente o colaborador avaliado pode contestar esta avaliacao."
    }

    precondition ($avaliacao_atual.status == "enviada") {
      error_type = "inputerror"
      error = "Somente avaliacoes enviadas podem ser contestadas."
    }

    db.add contestacao_avaliacao {
      data = {
        avaliacao_id  : $avaliacao_atual.id
        colaborador_id  : $colaborador_avaliado.id
        motivo             : $input.motivo
        status                : "aberta"
        updated_at               : "now"
      }
    } as $contestacao_criada

    // Auditoria: contestacao de avaliacao.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "contestar_avaliacao"
        recurso    : "contestacao_avaliacao"
        registro_id: $contestacao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Contestacao registrada. O RH ira revisar."
    contestacao : $contestacao_criada
  }

  guid = "conectahr-avaliacoes-contestar-post-0001"
}
