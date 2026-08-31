// Encerra a sessao mais recente do usuario autenticado. Aproximacao
// deliberada de "sessao atual": o token em si permanece criptografico
// e valido ate a expiracao natural (1h) em endpoints que nao verificam
// a tabela `sessao` — ver nota de escopo em design.md/tasks.md (2.2).
// Para encerrar uma sessao especifica (nao necessariamente a mais
// recente), use `sessoes/{id}/encerrar`.
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

    db.query sessao {
      where = $db.sessao.user_id == $usuario_autenticado.id && $db.sessao.ativa == true
      sort = {sessao.created_at: "desc"}
      return = {type: "single"}
    } as $sessao_recente

    conditional {
      if ($sessao_recente != null) {
        db.edit sessao {
          field_name = "id"
          field_value = $sessao_recente.id
          data = {ativa: false, revogada_em: "now", updated_at: "now"}
        } as $sessao_encerrada

        // Auditoria: logout.
        db.add auditoria {
          data = {
            user_id    : $usuario_autenticado.id
            acao       : "logout"
            recurso    : "sessao"
            registro_id: $sessao_recente.id
            resultado  : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Sessao encerrada com sucesso."
  }

  guid = "conectahr-auth-logout-post-0001"
}
