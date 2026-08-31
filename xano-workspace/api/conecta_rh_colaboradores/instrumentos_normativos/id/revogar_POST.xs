// Revoga definitivamente um instrumento normativo vigente ou suspenso.
query "instrumentos_normativos/{id}/revogar" verb=POST {
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
      error = "Somente RH ou ADMIN podem revogar instrumentos normativos."
    }

    db.get instrumento_normativo {
      field_name = "id"
      field_value = $input.id
    } as $instrumento_atual

    precondition ($instrumento_atual != null) {
      error_type = "notfound"
      error = "Instrumento normativo nao encontrado."
    }

    precondition ($instrumento_atual.status == "vigente" || $instrumento_atual.status == "suspenso") {
      error_type = "inputerror"
      error = "Somente instrumentos vigentes ou suspensos podem ser revogados."
    }

    db.edit instrumento_normativo {
      field_name = "id"
      field_value = $instrumento_atual.id
      data = {
        status     : "revogado"
        observacao : $input.motivo
        updated_at : "now"
      }
    } as $instrumento_revogado

    // Auditoria: revogacao de instrumento normativo.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "revogar_instrumento_normativo"
        recurso       : "instrumento_normativo"
        registro_id   : $instrumento_atual.id
        justificativa : $input.motivo
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Instrumento normativo revogado."
    instrumento : $instrumento_revogado
  }

  guid = "conectahr-instrumentos-normativos-revogar-post-0001"
}
