// Suspende um instrumento normativo vigente.
query "instrumentos_normativos/{id}/suspender" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text motivo filters=trim|min:5|max:1000
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
      error = "Somente RH ou ADMIN podem suspender instrumentos normativos."
    }

    db.get instrumento_normativo {
      field_name = "id"
      field_value = $input.id
    } as $instrumento_atual

    precondition ($instrumento_atual != null) {
      error_type = "notfound"
      error = "Instrumento normativo nao encontrado."
    }

    precondition ($instrumento_atual.status == "vigente") {
      error_type = "inputerror"
      error = "Somente instrumentos vigentes podem ser suspensos."
    }

    db.edit instrumento_normativo {
      field_name = "id"
      field_value = $instrumento_atual.id
      data = {
        status     : "suspenso"
        observacao : $input.motivo
        updated_at : "now"
      }
    } as $instrumento_suspenso

    // Auditoria: suspensao de instrumento normativo.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "suspender_instrumento_normativo"
        recurso       : "instrumento_normativo"
        registro_id   : $instrumento_atual.id
        justificativa : $input.motivo
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Instrumento normativo suspenso."
    instrumento : $instrumento_suspenso
  }

  guid = "conectahr-instrumentos-normativos-suspender-post-0001"
}
