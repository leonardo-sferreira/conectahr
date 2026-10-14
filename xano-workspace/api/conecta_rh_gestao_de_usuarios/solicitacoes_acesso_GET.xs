// Pedidos de alteracao de acesso (change pedido-de-acesso): RH e Admin veem todos, do mais recente
// ao mais antigo, com o nome da conta, de quem pediu e de quem decidiu. `status` filtra (opcional).
query solicitacoes_acesso verb=GET {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    text? status? filters=trim|lower
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

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin veem os pedidos de acesso."
    }

    db.query solicitacao_acesso {
      sort = {solicitacao_acesso.created_at: "desc"}
      return = {type: "list"}
    } as $pedidos

    var $lista {
      value = []
    }

    foreach ($pedidos) {
      each as $p {
        conditional {
          if (($input.status == null) || ($input.status == "") || ($p.status == $input.status)) {
            db.get user {
              field_name = "id"
              field_value = $p.usuario_id
              output = ["id", "nome", "email", "perfil", "ativo"]
            } as $conta

            db.get user {
              field_name = "id"
              field_value = $p.solicitante_user_id
              output = ["id", "nome"]
            } as $quem_pediu

            var $quem_decidiu_nome {
              value = null
            }

            conditional {
              if ($p.decidido_por_user_id != null) {
                db.get user {
                  field_name = "id"
                  field_value = $p.decidido_por_user_id
                  output = ["id", "nome"]
                } as $quem_decidiu

                var.update $quem_decidiu_nome {
                  value = ($quem_decidiu != null ? $quem_decidiu.nome : null)
                }
              }
            }

            var.update $lista {
              value = $lista|push:{id: $p.id, created_at: $p.created_at, usuario_id: $p.usuario_id, colaborador_id: $p.colaborador_id, nome: ($conta != null ? $conta.nome : null), email: ($conta != null ? $conta.email : null), perfil_hoje: ($conta != null ? $conta.perfil : null), perfil_atual: $p.perfil_atual, perfil_solicitado: $p.perfil_solicitado, justificativa: $p.justificativa, status: $p.status, solicitante_user_id: $p.solicitante_user_id, solicitante_nome: ($quem_pediu != null ? $quem_pediu.nome : null), decidido_por_nome: $quem_decidiu_nome, data_decisao: $p.data_decisao, motivo_decisao: $p.motivo_decisao}
            }
          }
        }
      }
    }
  }

  response = {
    sucesso     : true
    quantidade  : ($lista|count)
    solicitacoes: $lista
  }

  guid = "conectahr-solicitacoes-acesso-get-0001"
}
