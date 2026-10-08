// Encerra a sessao do proprio token (extras.sessao_id). Como todo endpoint
// autenticado valida a sessao do token, o token deixa de funcionar na hora.
// Para encerrar outra sessao, use `sessoes/{id}/encerrar`.
query "auth/logout" verb=POST {
  api_group = "ConectaRH — Autenticação"
  auth = "user"

  input {
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

    // Encerra exatamente a sessao do token (validada pela guarda acima);
    // as demais sessoes do usuario continuam ativas.
    db.edit sessao {
      field_name = "id"
      field_value = $sessao_token.id
      data = {ativa: false, revogada_em: "now", updated_at: "now"}
    } as $sessao_encerrada

    // Auditoria: logout.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "logout"
        recurso    : "sessao"
        registro_id: $sessao_token.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Sessao encerrada com sucesso."
  }

  guid = "conectahr-auth-logout-post-0001"
}
