// Lista as notificacoes internas do usuario autenticado, mais recentes
// primeiro (item 5.11).
query "minhas_notificacoes" verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    db.query notificacao_interna {
      where = $db.notificacao_interna.destinatario_user_id == $usuario_autenticado.id
      sort = {notificacao_interna.created_at: "desc"}
      return = {type: "list"}
    } as $notificacoes

    var $total_nao_lidas {
      value = 0
    }

    foreach ($notificacoes) {
      each as $notificacao_item {
        conditional {
          if ($notificacao_item.lida == false) {
            var.update $total_nao_lidas {
              value = $total_nao_lidas + 1
            }
          }
        }
      }
    }
  }

  response = {
    sucesso        : true
    total_nao_lidas: $total_nao_lidas
    notificacoes   : $notificacoes
  }

  guid = "conectahr-minhas-notificacoes-get-0001"
}
