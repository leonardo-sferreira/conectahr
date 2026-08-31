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
  }

  response = {
    sucesso  : true
    mensagem : "Regra enviada para aprovacao."
    override : $override_atualizado
  }

  guid = "conectahr-regras-override-enviar-aprovacao-post-0001"
}
