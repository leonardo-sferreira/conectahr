// Encerra uma sessao especifica do usuario autenticado, sem afetar as
// demais (Requirement: Sessoes e dispositivos - "Encerramento de
// dispositivo"). Um usuario so pode encerrar as proprias sessoes.
query "auth/sessoes/{id}/encerrar" verb=POST {
  api_group = "ConectaRH — Autenticação"
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

    db.get sessao {
      field_name = "id"
      field_value = $input.id
    } as $sessao_alvo

    precondition ($sessao_alvo != null) {
      error_type = "notfound"
      error = "Sessao nao encontrada."
    }

    precondition ($sessao_alvo.user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce so pode encerrar as proprias sessoes."
    }

    precondition ($sessao_alvo.ativa) {
      error_type = "inputerror"
      error = "Esta sessao ja esta encerrada."
    }

    db.edit sessao {
      field_name = "id"
      field_value = $sessao_alvo.id
      data = {ativa: false, revogada_em: "now", updated_at: "now"}
    } as $sessao_encerrada

    // Auditoria: encerramento de sessao especifica.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "encerrar_sessao"
        recurso    : "sessao"
        registro_id: $sessao_alvo.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Sessao encerrada com sucesso."
    sessao  : $sessao_encerrada
  }

  guid = "conectahr-auth-sessoes-encerrar-post-0001"
}
