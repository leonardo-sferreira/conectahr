// Remove uma pergunta da FAQ de um beneficio (tarefa 85): desativa, sem apagar. Somente RH ou Admin.
query "beneficio_faq/{id}/remover" verb=POST {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.get beneficio_faq {
      field_name = "id"
      field_value = $input.id
    } as $faq

    precondition ($faq != null && $faq.ativo) {
      error_type = "notfound"
      error = "Pergunta nao encontrada."
    }

    db.get beneficio {
      field_name = "id"
      field_value = $faq.beneficio_id
    } as $beneficio

    db.edit beneficio_faq {
      field_name = "id"
      field_value = $faq.id
      data = {ativo: false, atualizado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
    } as $faq_removida

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "remover_faq_beneficio"
        recurso    : "beneficio_faq"
        registro_id: $faq.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso: true
  }

  guid = "conectahr-beneficio-faq-remover-post-0001"
}
