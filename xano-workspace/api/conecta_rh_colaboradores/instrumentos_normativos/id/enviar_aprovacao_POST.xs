// Envia um instrumento normativo (rascunho) para aprovacao.
query "instrumentos_normativos/{id}/enviar_aprovacao" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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
      error = "Somente RH ou ADMIN podem enviar instrumentos para aprovacao."
    }

    db.get instrumento_normativo {
      field_name = "id"
      field_value = $input.id
    } as $instrumento_atual

    precondition ($instrumento_atual != null) {
      error_type = "notfound"
      error = "Instrumento normativo nao encontrado."
    }

    precondition ($instrumento_atual.status == "rascunho") {
      error_type = "inputerror"
      error = "Somente instrumentos em rascunho podem ser enviados para aprovacao."
    }

    db.edit instrumento_normativo {
      field_name = "id"
      field_value = $instrumento_atual.id
      data = {status: "pendente_aprovacao", updated_at: "now"}
    } as $instrumento_atualizado

    // Auditoria: envio de instrumento normativo para aprovacao (item 7.11).
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "enviar_instrumento_normativo_aprovacao"
        recurso       : "instrumento_normativo"
        registro_id   : $instrumento_atual.id
        valor_anterior: "rascunho"
        valor_novo    : "pendente_aprovacao"
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Instrumento enviado para aprovacao."
    instrumento : $instrumento_atualizado
  }

  guid = "conectahr-instrumentos-normativos-enviar-aprovacao-post-0001"
}
