// Arquiva um comunicado (tela "Comunicados e FAQ" do RH, Figma 245:594; tarefa 46 da change
// concluir-frontend-streamlit): ele sai do Inicio e da tela de todos, sem apagar o registro. RH e Admin. Fica na
// auditoria. Arquivar de novo e recusado.
query "comunicados/{id}/arquivar" verb=POST {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem arquivar comunicados."
    }

    db.get comunicado {
      field_name = "id"
      field_value = $input.id
    } as $comunicado_alvo

    precondition ($comunicado_alvo != null) {
      error_type = "notfound"
      error = "Comunicado nao encontrado."
    }

    precondition ($comunicado_alvo.ativo) {
      error_type = "inputerror"
      error = "Este comunicado ja esta arquivado."
    }

    db.edit comunicado {
      field_name = "id"
      field_value = $comunicado_alvo.id
      data = {ativo: false, updated_at: "now"}
    } as $comunicado_arquivado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "arquivar_comunicado"
        recurso    : "comunicado"
        registro_id: $comunicado_alvo.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Comunicado arquivado."
  }

  guid = "conectahr-comunicados-arquivar-post-0001"
}
