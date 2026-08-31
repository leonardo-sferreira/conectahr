// Encerra todas as sessoes ativas do usuario autenticado, exceto a
// mais recente (aproximacao de "sessao atual" - ver logout_POST.xs).
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

    db.query sessao {
      where = $db.sessao.user_id == $usuario_autenticado.id && $db.sessao.ativa == true
      sort = {sessao.created_at: "desc"}
      return = {type: "list"}
    } as $sessoes_ativas

    var $total_encerradas {
      value = 0
    }

    var $indice {
      value = 0
    }

    foreach ($sessoes_ativas) {
      each as $sessao_item {
        // Preserva a primeira da lista (mais recente); encerra as demais.
        conditional {
          if ($indice > 0) {
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

        var.update $indice {
          value = $indice + 1
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
