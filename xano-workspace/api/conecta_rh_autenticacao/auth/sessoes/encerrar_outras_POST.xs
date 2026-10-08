// Encerra todas as sessoes ativas do usuario autenticado, exceto a do
// proprio token (extras.sessao_id), que segue valida.
// Util para "encerrar todos os outros dispositivos".
query "auth/sessoes/encerrar_outras" verb=POST {
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

    db.query sessao {
      where = $db.sessao.user_id == $usuario_autenticado.id && $db.sessao.ativa == true
      sort = {sessao.created_at: "desc"}
      return = {type: "list"}
    } as $sessoes_ativas

    var $total_encerradas {
      value = 0
    }

    foreach ($sessoes_ativas) {
      each as $sessao_item {
        // Preserva a sessao do token; encerra as demais.
        conditional {
          if ($sessao_item.id != $sessao_token.id) {
            db.edit sessao {
              field_name = "id"
              field_value = $sessao_item.id
              data = {ativa: false, revogada_em: "now", updated_at: "now"}
            } as $sessao_encerrada

            var.update $total_encerradas {
              value = $total_encerradas + 1
            }
          }
        }
      }
    }

    conditional {
      if ($total_encerradas > 0) {
        db.add auditoria {
          data = {
            user_id    : $usuario_autenticado.id
            acao       : "encerrar_outras_sessoes"
            recurso    : "sessao"
            valor_novo : ($total_encerradas|to_text)
            resultado  : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso          : true
    mensagem         : "Sessoes encerradas com sucesso."
    total_encerradas : $total_encerradas
  }

  guid = "conectahr-auth-sessoes-encerrar-outras-post-0001"
}
