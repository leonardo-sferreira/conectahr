// Lista as solicitações de desligamento para análise do RH, as mais antigas primeiro.
// Tela Desligamentos (change fluxo-de-desligamento, D2): o status é opcional (vazio = todos), a
// resposta traz as contagens por status (e os concluídos no ano) e, em cada pedido, os nomes da
// pessoa, do departamento, do cargo, de quem pediu e do responsável do RH. Sem `||` no where.
query solicitacoes_desligamento verb=GET {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    text? status? filters=trim
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
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
  
    // Contas inativas não podem consultar solicitações.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // A fila de desligamentos é exclusiva do RH.
    precondition ($perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode consultar solicitações de desligamento."
    }
  
    // Normaliza o status recebido.
    var $status_normalizado {
      value = (($input.status == null) || ($input.status == "")) ? "" : ($input.status|trim|to_lower)
    }
  
    // Valida os valores configurados no Enum.
    precondition ($status_normalizado == "" || $status_normalizado == "pendente" || $status_normalizado == "em_analise" || $status_normalizado == "agendado" || $status_normalizado == "rejeitada" || $status_normalizado == "cancelada" || $status_normalizado == "concluido") {
      error_type = "inputerror"
      error = "Status inválido. Use pendente, em_analise, agendado, rejeitada, cancelada ou concluido."
    }
  
    db.query solicitacao_desligamento {
      sort = {solicitacao_desligamento.created_at: "asc"}
      return = {type: "list"}
    } as $todas

    var $ano_atual {
      value = now|format_timestamp:"Y":"America/Sao_Paulo"
    }

    var $contagens {
      value = {pendente: 0, em_analise: 0, agendado: 0, rejeitada: 0, cancelada: 0, concluido: 0, concluido_no_ano: 0}
    }

    var $solicitacoes {
      value = []
    }

    foreach ($todas) {
      each as $s {
        var.update $contagens {
          value = $contagens|set:$s.status:(($contagens|get:$s.status) + 1)
        }

        conditional {
          if (($s.status == "concluido") && ($s.data_conclusao != null) && (($s.data_conclusao|format_timestamp:"Y":"America/Sao_Paulo") == $ano_atual)) {
            var.update $contagens {
              value = $contagens|set:"concluido_no_ano":(($contagens|get:"concluido_no_ano") + 1)
            }
          }
        }

        conditional {
          if (($status_normalizado == "") || ($s.status == $status_normalizado)) {
            db.get colaborador {
              field_name = "id"
              field_value = $s.colaborador_id
              output = ["id", "nome", "departamento_id", "cargo_id", "user_id"]
            } as $pessoa

            var $departamento_nome {
              value = null
            }

            var $cargo_nome {
              value = null
            }

            conditional {
              if (($pessoa != null) && ($pessoa.departamento_id != null)) {
                db.get departamento {
                  field_name = "id"
                  field_value = $pessoa.departamento_id
                  output = ["id", "nome"]
                } as $dep_pessoa

                var.update $departamento_nome {
                  value = ($dep_pessoa != null ? $dep_pessoa.nome : null)
                }
              }
            }

            conditional {
              if (($pessoa != null) && ($pessoa.cargo_id != null)) {
                db.get cargo {
                  field_name = "id"
                  field_value = $pessoa.cargo_id
                  output = ["id", "nome"]
                } as $cargo_pessoa

                var.update $cargo_nome {
                  value = ($cargo_pessoa != null ? $cargo_pessoa.nome : null)
                }
              }
            }

            db.get user {
              field_name = "id"
              field_value = $s.solicitante_user_id
              output = ["id", "nome"]
            } as $solicitante

            var $responsavel_nome {
              value = null
            }

            conditional {
              if ($s.responsavel_rh_user_id != null) {
                db.get user {
                  field_name = "id"
                  field_value = $s.responsavel_rh_user_id
                  output = ["id", "nome"]
                } as $responsavel

                var.update $responsavel_nome {
                  value = ($responsavel != null ? $responsavel.nome : null)
                }
              }
            }

            var.update $solicitacoes {
              value = $solicitacoes|push:($s|set:"colaborador_nome":($pessoa != null ? $pessoa.nome : null)|set:"colaborador_user_id":($pessoa != null ? $pessoa.user_id : null)|set:"departamento":$departamento_nome|set:"cargo":$cargo_nome|set:"solicitante_nome":($solicitante != null ? $solicitante.nome : null)|set:"responsavel_rh_nome":$responsavel_nome)
            }
          }
        }
      }
    }

    var $quantidade {
      value = $solicitacoes|count
    }
  }

  response = {
    sucesso     : true
    status      : $status_normalizado
    quantidade  : $quantidade
    contagens   : $contagens
    solicitacoes: $solicitacoes
  }

  guid = "YwwbapGnz7ci80sugRFLhkw55PA"
}