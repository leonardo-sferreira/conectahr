// Lista as notificacoes internas do usuario autenticado, mais recentes
// primeiro (item 5.11), com a data de criacao (criada_em) e no maximo 50.
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

    // A lista que vai para a tela (sino): as 50 mais recentes, com a data de criacao, que e
    // privada na tabela e nao sairia na resposta (12/10/2026, sino do topo).
    var $lista {
      value = []
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

        conditional {
          if (($lista|count) < 50) {
            var.update $lista {
              value = $lista|push:{id: $notificacao_item.id, tipo: $notificacao_item.tipo, titulo: $notificacao_item.titulo, mensagem: $notificacao_item.mensagem, recurso: $notificacao_item.recurso, registro_id: $notificacao_item.registro_id, lida: $notificacao_item.lida, lida_em: $notificacao_item.lida_em, criada_em: $notificacao_item.created_at}
            }
          }
        }
      }
    }
  }

  response = {
    sucesso        : true
    total_nao_lidas: $total_nao_lidas
    notificacoes   : $lista
  }

  guid = "conectahr-minhas-notificacoes-get-0001"
}
