// Contestacoes das avaliacoes de relacao gestor feitas por quem pede (change backend-gestor-pendencias, D5), com a
// resposta do Gestor e a do RH. So o avaliador ve as dele; nenhum outro perfil ganha acesso por aqui.
query contestacoes_equipe verb=GET {
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

    db.query avaliacao {
      where = $db.avaliacao.user_id == $usuario_autenticado.id && $db.avaliacao.relacao_avaliador == "gestor"
      return = {type: "list"}
      output = ["id", "colaborador_id", "ciclo_avaliacao_id", "nota", "nota_original", "status"]
    } as $avaliacoes_minhas

    var $ids_texto {
      value = ","
    }

    foreach ($avaliacoes_minhas) {
      each as $a {
        var.update $ids_texto {
          value = $ids_texto ~ ($a.id|to_text) ~ ","
        }
      }
    }

    db.query contestacao_avaliacao {
      sort = {contestacao_avaliacao.id: "desc"}
      return = {type: "list"}
    } as $todas

    var $lista {
      value = []
    }

    foreach ($todas) {
      each as $c {
        conditional {
          if ($ids_texto|contains:("," ~ ($c.avaliacao_id|to_text) ~ ",")) {
            var $av_c {
              value = null
            }

            foreach ($avaliacoes_minhas) {
              each as $a2 {
                conditional {
                  if ($a2.id == $c.avaliacao_id) {
                    var.update $av_c {
                      value = $a2
                    }
                  }
                }
              }
            }

            db.get colaborador {
              field_name = "id"
              field_value = $c.colaborador_id
              output = ["id", "nome"]
            } as $pessoa_c

            db.get ciclo_avaliacao {
              field_name = "id"
              field_value = $av_c.ciclo_avaliacao_id
              output = ["id", "nome"]
            } as $ciclo_c

            var $nome_pessoa {
              value = ($pessoa_c != null) ? $pessoa_c.nome : null
            }

            var $nome_ciclo {
              value = ($ciclo_c != null) ? $ciclo_c.nome : null
            }

            var.update $lista {
              value = $lista|push:{id: $c.id, avaliacao_id: $c.avaliacao_id, colaborador_nome: $nome_pessoa, ciclo_nome: $nome_ciclo, ciclo_avaliacao_id: $av_c.ciclo_avaliacao_id, nota: $av_c.nota, nota_original: $av_c.nota_original, motivo: $c.motivo, status: $c.status, decisao_gestor: $c.decisao_gestor, nota_revisada: $c.nota_revisada, resposta_gestor: $c.resposta_gestor, respondido_gestor_em: $c.respondido_gestor_em, resposta_rh: $c.resposta_revisao, data_revisao: $c.data_revisao}
            }
          }
        }
      }
    }
  }

  response = {
    sucesso      : true
    contestacoes : $lista
  }

  guid = "conectahr-contestacoes-equipe-get-0001"
}
