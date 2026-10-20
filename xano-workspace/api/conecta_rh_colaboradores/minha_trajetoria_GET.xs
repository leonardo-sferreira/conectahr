// Trajetoria do colaborador autenticado (change trajetoria-do-colaborador, D1 e D2):
// plano de carreira, 360 do ciclo em andamento, avaliacoes a preencher, avaliacoes
// enviadas sobre a pessoa, metas e PDI ativos e reconhecimentos recebidos, numa
// chamada so (o plano gratuito aceita 10 requisicoes a cada 20 s). So leitura.
// Pares e subordinados ficam anonimos: so a contagem e a relacao, sem o nome.
query "minha_trajetoria" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    // Plano de carreira: so informa o proximo nivel, nunca promove.
    var $proximo_nivel {
      value = null
    }

    conditional {
      if ($colaborador_autenticado.nivel == "l1") {
        var.update $proximo_nivel {
          value = "l2"
        }
      }
    }

    conditional {
      if ($colaborador_autenticado.nivel == "l2") {
        var.update $proximo_nivel {
          value = "l3"
        }
      }
    }

    conditional {
      if ($colaborador_autenticado.nivel == "l3") {
        var.update $proximo_nivel {
          value = "l4"
        }
      }
    }

    conditional {
      if ($colaborador_autenticado.nivel == "l4") {
        var.update $proximo_nivel {
          value = "l5"
        }
      }
    }

    var $competencias_proximo_nivel {
      value = []
    }

    conditional {
      if ($proximo_nivel != null) {
        db.query competencia_avaliacao {
          where = $db.competencia_avaliacao.nivel == $proximo_nivel && $db.competencia_avaliacao.ativo == true
          sort = {competencia_avaliacao.nome: "asc"}
          return = {type: "list"}
          output = ["id", "nome"]
        } as $competencias_encontradas

        var.update $competencias_proximo_nivel {
          value = $competencias_encontradas
        }
      }
    }

    // Ciclo em andamento mais recente.
    db.query ciclo_avaliacao {
      where = $db.ciclo_avaliacao.status == "em_andamento"
      sort = {ciclo_avaliacao.created_at: "desc"}
      return = {type: "single"}
      output = ["id", "nome", "data_fim"]
    } as $ciclo

    // Avaliacoes sobre a pessoa: 360 do ciclo e as enviadas (qualquer ciclo).
    var $auto_status {
      value = null
    }

    var $gestor_status {
      value = null
    }

    var $gestor_nome {
      value = null
    }

    var $pares_total {
      value = 0
    }

    var $pares_enviadas {
      value = 0
    }

    var $recebidas {
      value = []
    }

    db.query avaliacao {
      where = $db.avaliacao.colaborador_id == $colaborador_autenticado.id
      sort = {avaliacao.created_at: "desc"}
      return = {type: "list"}
    } as $sobre_mim

    foreach ($sobre_mim) {
      each as $a {
        conditional {
          if (($ciclo != null) && ($a.ciclo_avaliacao_id == $ciclo.id) && ($a.status != "cancelada")) {
            conditional {
              if ($a.relacao_avaliador == "autoavaliacao") {
                var.update $auto_status {
                  value = $a.status
                }
              }
            }

            conditional {
              if ($a.relacao_avaliador == "gestor") {
                db.get user {
                  field_name = "id"
                  field_value = $a.user_id
                  output = ["id", "nome"]
                } as $gestor_avaliador

                var.update $gestor_status {
                  value = $a.status
                }

                var.update $gestor_nome {
                  value = ($gestor_avaliador != null ? $gestor_avaliador.nome : null)
                }
              }
            }

            conditional {
              if ($a.relacao_avaliador == "par") {
                var.update $pares_total {
                  value = $pares_total + 1
                }

                conditional {
                  if ($a.status == "enviada") {
                    var.update $pares_enviadas {
                      value = $pares_enviadas + 1
                    }
                  }
                }
              }
            }
          }
        }

        conditional {
          if (($a.status == "enviada") && ($a.relacao_avaliador != "autoavaliacao")) {
            // Nome do avaliador so para gestor e RH (pares e subordinados ficam anonimos).
            var $avaliador_nome {
              value = null
            }

            conditional {
              if (($a.relacao_avaliador == "gestor") || ($a.relacao_avaliador == "rh")) {
                db.get user {
                  field_name = "id"
                  field_value = $a.user_id
                  output = ["id", "nome"]
                } as $avaliador

                var.update $avaliador_nome {
                  value = ($avaliador != null ? $avaliador.nome : null)
                }
              }
            }

            var $ciclo_nome_recebida {
              value = null
            }

            conditional {
              if ($a.ciclo_avaliacao_id != null) {
                db.get ciclo_avaliacao {
                  field_name = "id"
                  field_value = $a.ciclo_avaliacao_id
                  output = ["id", "nome"]
                } as $ciclo_recebida

                var.update $ciclo_nome_recebida {
                  value = ($ciclo_recebida != null ? $ciclo_recebida.nome : null)
                }
              }
            }

            db.query contestacao_avaliacao {
              where = $db.contestacao_avaliacao.avaliacao_id == $a.id
              sort = {contestacao_avaliacao.created_at: "desc"}
              return = {type: "single"}
              output = ["id", "status", "resposta_revisao", "created_at"]
            } as $contestacao

            var.update $recebidas {
              value = $recebidas|push:{id: $a.id, relacao: $a.relacao_avaliador, nota: $a.nota, comentario: $a.comentario, data_avaliacao: $a.data_avaliacao, ciclo_nome: $ciclo_nome_recebida, avaliador_nome: $avaliador_nome, contestacao_status: ($contestacao != null ? $contestacao.status : null), contestacao_resposta: ($contestacao != null ? $contestacao.resposta_revisao : null)}
            }
          }
        }
      }
    }

    // Avaliacoes que a pessoa tem a preencher.
    var $a_preencher {
      value = []
    }

    db.query avaliacao {
      where = $db.avaliacao.user_id == $usuario_autenticado.id
      sort = {avaliacao.created_at: "asc"}
      return = {type: "list"}
      output = ["id", "colaborador_id", "ciclo_avaliacao_id", "relacao_avaliador", "status"]
    } as $designadas

    foreach ($designadas) {
      each as $d {
        conditional {
          if (($d.status == "pendente") || ($d.status == "em_andamento")) {
            db.get colaborador {
              field_name = "id"
              field_value = $d.colaborador_id
              output = ["id", "nome"]
            } as $avaliado

            var $ciclo_nome_designada {
              value = null
            }

            conditional {
              if ($d.ciclo_avaliacao_id != null) {
                db.get ciclo_avaliacao {
                  field_name = "id"
                  field_value = $d.ciclo_avaliacao_id
                  output = ["id", "nome"]
                } as $ciclo_designada

                var.update $ciclo_nome_designada {
                  value = ($ciclo_designada != null ? $ciclo_designada.nome : null)
                }
              }
            }

            var.update $a_preencher {
              value = $a_preencher|push:{id: $d.id, relacao: $d.relacao_avaliador, status: $d.status, avaliado_nome: ($avaliado != null ? $avaliado.nome : null), ciclo_nome: $ciclo_nome_designada}
            }
          }
        }
      }
    }

    // Metas e PDI que nao estao concluidos nem cancelados.
    db.query meta_avaliacao {
      where = $db.meta_avaliacao.colaborador_id == $colaborador_autenticado.id && $db.meta_avaliacao.status != "concluida" && $db.meta_avaliacao.status != "cancelada"
      sort = {meta_avaliacao.data_prazo: "asc"}
      return = {type: "list"}
      output = ["id", "titulo", "descricao", "indicador", "data_prazo", "progresso_percentual", "status", "data_checkin_realizado"]
    } as $metas

    db.query pdi {
      where = $db.pdi.colaborador_id == $colaborador_autenticado.id && $db.pdi.status != "concluido" && $db.pdi.status != "cancelado"
      sort = {pdi.data_prazo: "asc"}
      return = {type: "list"}
      output = ["id", "titulo", "descricao", "acao_desenvolvimento", "data_inicio", "data_prazo", "progresso_percentual", "status", "evidencia"]
    } as $pdi

    // Reconhecimentos recebidos ativos, com o nome de quem enviou.
    var $reconhecimentos {
      value = []
    }

    db.query reconhecimento {
      where = $db.reconhecimento.destinatario_colaborador_id == $colaborador_autenticado.id && $db.reconhecimento.status == "ativo"
      sort = {reconhecimento.created_at: "desc"}
      return = {type: "list"}
      output = ["id", "created_at", "remetente_user_id", "titulo", "mensagem", "visibilidade"]
    } as $recebidos

    foreach ($recebidos) {
      each as $r {
        db.get user {
          field_name = "id"
          field_value = $r.remetente_user_id
          output = ["id", "nome", "perfil"]
        } as $remetente

        var.update $reconhecimentos {
          value = $reconhecimentos|push:{id: $r.id, created_at: $r.created_at, titulo: $r.titulo, mensagem: $r.mensagem, visibilidade: $r.visibilidade, remetente_nome: ($remetente != null ? $remetente.nome : null), remetente_perfil: ($remetente != null ? $remetente.perfil : null)}
        }
      }
    }
  }

  response = {
    sucesso                   : true
    colaborador_id            : $colaborador_autenticado.id
    nivel_atual               : $colaborador_autenticado.nivel
    proximo_nivel             : $proximo_nivel
    competencias_proximo_nivel: $competencias_proximo_nivel
    ciclo                     : $ciclo
    autoavaliacao_status      : $auto_status
    gestor_status             : $gestor_status
    gestor_nome               : $gestor_nome
    pares_total               : $pares_total
    pares_enviadas            : $pares_enviadas
    a_preencher               : $a_preencher
    recebidas                 : $recebidas
    metas                     : $metas
    pdi                       : $pdi
    reconhecimentos           : $reconhecimentos
  }

  guid = "conectahr-minha-trajetoria-get-0001"
}
