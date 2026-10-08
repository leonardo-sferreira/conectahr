// Envia uma regra_override (rascunho) para aprovacao.
query "regras_override/{id}/enviar_aprovacao" verb=POST {
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
      error = "Somente RH ou ADMIN podem enviar regras de override para aprovacao."
    }

    db.get regra_override {
      field_name = "id"
      field_value = $input.id
    } as $override_atual

    precondition ($override_atual != null) {
      error_type = "notfound"
      error = "Regra de override nao encontrada."
    }

    precondition ($override_atual.status == "rascunho") {
      error_type = "inputerror"
      error = "Somente regras em rascunho podem ser enviadas para aprovacao."
    }

    db.edit regra_override {
      field_name = "id"
      field_value = $override_atual.id
      data = {status: "pendente_aprovacao", updated_at: "now"}
    } as $override_atualizado

    // Auditoria: envio de regra de override para aprovacao (item 7.11).
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "enviar_regra_override_aprovacao"
        recurso       : "regra_override"
        registro_id   : $override_atual.id
        valor_anterior: "rascunho"
        valor_novo    : "pendente_aprovacao"
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Regra enviada para aprovacao."
    override : $override_atualizado
  }

  guid = "conectahr-regras-override-enviar-aprovacao-post-0001"
}
