// Rejeita um instrumento normativo pendente de aprovacao.
query "instrumentos_normativos/{id}/rejeitar" verb=POST {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem rejeitar instrumentos normativos."
    }

    db.get instrumento_normativo {
      field_name = "id"
      field_value = $input.id
    } as $instrumento_atual

    precondition ($instrumento_atual != null) {
      error_type = "notfound"
      error = "Instrumento normativo nao encontrado."
    }

    precondition ($instrumento_atual.status == "pendente_aprovacao") {
      error_type = "inputerror"
      error = "Somente instrumentos pendentes de aprovacao podem ser rejeitados."
    }

    db.edit instrumento_normativo {
      field_name = "id"
      field_value = $instrumento_atual.id
      data = {
        status     : "rejeitado"
        observacao : $input.motivo
        updated_at : "now"
      }
    } as $instrumento_rejeitado

    // Auditoria: rejeicao de instrumento normativo.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "rejeitar_instrumento_normativo"
        recurso       : "instrumento_normativo"
        registro_id   : $instrumento_atual.id
        justificativa : $input.motivo
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Instrumento normativo rejeitado."
    instrumento : $instrumento_rejeitado
  }

  guid = "conectahr-instrumentos-normativos-rejeitar-post-0001"
}
