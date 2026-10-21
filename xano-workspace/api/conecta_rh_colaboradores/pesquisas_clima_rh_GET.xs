// Pesquisas de clima para o RH (change pesquisa-clima-e-avaliacao-360, D3): todas, das mais novas
// para as mais antigas, com a situacao (agendada, aberta ou encerrada), as perguntas, quantas pessoas
// responderam (participacoes na primeira pergunta; o envio e de tudo de uma vez) e quantas podem responder
// (fichas que nao estao desligadas), no geral e por departamento (Figma 249:4645, "Adesao"; a adesao
// conta quem respondeu, nunca o que respondeu). Nao mostra quem respondeu. So RH e Admin.
query "pesquisas_clima_rh" verb=GET {
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.query pesquisa_clima {
      sort = {pesquisa_clima.created_at: "desc"}
      return = {type: "list"}
    } as $todas_pesquisas

    db.query pergunta_clima {
      sort = {pergunta_clima.ordem: "asc"}
      return = {type: "list"}
    } as $todas_perguntas

    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      return = {type: "list"}
      output = ["id", "departamento_id"]
    } as $fichas_elegiveis

    var $elegiveis {
      value = $fichas_elegiveis|count
    }

    db.query departamento {
      sort = {departamento.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome"]
    } as $departamentos

    var $pesquisas {
      value = []
    }

    foreach ($todas_pesquisas) {
      each as $pesquisa {
        var $perguntas_da_pesquisa {
          value = []
        }

        foreach ($todas_perguntas) {
          each as $pergunta {
            conditional {
              if ($pergunta.pesquisa_clima_id == $pesquisa.id) {
                var.update $perguntas_da_pesquisa {
                  value = $perguntas_da_pesquisa|push:{id: $pergunta.id, texto: $pergunta.texto, ordem: $pergunta.ordem, escala: $pergunta.escala, dimensao: $pergunta.dimensao, sentido: $pergunta.sentido}
                }
              }
            }
          }
        }

        var $participantes {
          value = 0
        }

        var $participantes_texto {
          value = ","
        }

        conditional {
          if (($perguntas_da_pesquisa|count) > 0) {
            var $primeira_pergunta {
              value = $perguntas_da_pesquisa|first
            }

            db.query resposta_clima_participacao {
              where = $db.resposta_clima_participacao.pergunta_clima_id == $primeira_pergunta.id
              return = {type: "list"}
              output = ["colaborador_id"]
            } as $participacoes_primeira

            var.update $participantes {
              value = $participacoes_primeira|count
            }

            foreach ($participacoes_primeira) {
              each as $participacao {
                var.update $participantes_texto {
                  value = $participantes_texto ~ ($participacao.colaborador_id|to_text) ~ ","
                }
              }
            }
          }
        }

        // Adesao por departamento: fichas elegiveis do departamento e quantas delas responderam.
        var $adesao_departamentos {
          value = []
        }

        foreach ($departamentos) {
          each as $departamento_item {
            var $dep_elegiveis {
              value = 0
            }

            var $dep_participantes {
              value = 0
            }

            foreach ($fichas_elegiveis) {
              each as $ficha {
                conditional {
                  if ($ficha.departamento_id == $departamento_item.id) {
                    var.update $dep_elegiveis {
                      value = $dep_elegiveis + 1
                    }

                    var $agulha_ficha {
                      value = "," ~ ($ficha.id|to_text) ~ ","
                    }

                    conditional {
                      if ($participantes_texto|contains:$agulha_ficha) {
                        var.update $dep_participantes {
                          value = $dep_participantes + 1
                        }
                      }
                    }
                  }
                }
              }
            }

            conditional {
              if ($dep_elegiveis > 0) {
                var.update $adesao_departamentos {
                  value = $adesao_departamentos|push:{departamento_id: $departamento_item.id, nome: $departamento_item.nome, participantes: $dep_participantes, elegiveis: $dep_elegiveis}
                }
              }
            }
          }
        }

        var $situacao {
          value = "aberta"
        }

        conditional {
          if (($pesquisa.ativo == false) || ($pesquisa.data_fim < $hoje)) {
            var.update $situacao {
              value = "encerrada"
            }
          }

          elseif ($pesquisa.data_inicio > $hoje) {
            var.update $situacao {
              value = "agendada"
            }
          }
        }

        var.update $pesquisas {
          value = $pesquisas|push:{
            id               : $pesquisa.id
            titulo           : $pesquisa.titulo
            tipo             : $pesquisa.tipo
            descricao        : $pesquisa.descricao
            data_inicio      : $pesquisa.data_inicio
            data_fim         : $pesquisa.data_fim
            minimo_respostas : $pesquisa.minimo_respostas
            situacao         : $situacao
            participantes    : $participantes
            adesao_departamentos: $adesao_departamentos
            perguntas        : $perguntas_da_pesquisa
          }
        }
      }
    }
  }

  response = {
    sucesso   : true
    hoje      : $hoje
    elegiveis : $elegiveis
    pesquisas : $pesquisas
  }

  guid = "conectahr-pesquisas-clima-rh-get-0001"
}
