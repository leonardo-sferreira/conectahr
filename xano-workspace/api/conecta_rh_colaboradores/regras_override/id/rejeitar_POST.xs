// Rejeita uma regra de override pendente de aprovacao, com motivo (change tela-de-regras, D4).
// Como na aprovacao, quem criou a regra nao a rejeita. So RH e Admin; auditado com o motivo.
query "regras_override/{id}/rejeitar" verb=POST {
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.get regra_override {
      field_name = "id"
      field_value = $input.id
    } as $override_atual

    precondition ($override_atual != null) {
      error_type = "notfound"
      error = "Regra de override nao encontrada."
    }

    precondition ($override_atual.status == "pendente_aprovacao") {
      error_type = "inputerror"
      error = "Somente regras pendentes de aprovacao podem ser rejeitadas."
    }

    precondition ($override_atual.criado_por_user_id != $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Quem criou a regra nao pode rejeita-la."
    }

    db.edit regra_override {
      field_name = "id"
      field_value = $override_atual.id
      data = {status: "rejeitada", updated_at: "now"}
    } as $override_rejeitado

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "rejeitar_regra_override"
        recurso       : "regra_override"
        registro_id   : $override_atual.id
        valor_anterior: "pendente_aprovacao"
        valor_novo    : "rejeitada"
        justificativa : $input.motivo
        resultado     : "sucesso"
      }
    } as $evento_auditoria

    function.run "ConectaHR/notificar" {
      input = {destinatario_user_id: $override_atual.criado_por_user_id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_decidido", titulo: "Regra rejeitada", mensagem: "Sua regra de override foi rejeitada. Motivo: " ~ $input.motivo, recurso: "regra_override", registro_id: $override_atual.id}
    } as $aviso_autor
  }

  response = {
    sucesso : true
    mensagem: "Regra de override rejeitada."
    override: $override_rejeitado
  }

  guid = "conectahr-regras-override-rejeitar-post-0001"
}
