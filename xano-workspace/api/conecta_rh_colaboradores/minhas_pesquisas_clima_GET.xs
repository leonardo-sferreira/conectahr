// Pesquisas de clima da pessoa (change pesquisa-clima-e-avaliacao-360, D2): as que ja abriram,
// das mais novas para as mais antigas, cada uma com a situacao (aberta ou encerrada), se a pessoa ja
// respondeu e, nas abertas que faltam responder, as perguntas. Qualquer perfil com ficha.
// Uma chamada so (limite de requisicoes do plano).
query "minhas_pesquisas_clima" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.query pesquisa_clima {
      where = $db.pesquisa_clima.data_inicio <= $hoje
      sort = {pesquisa_clima.data_inicio: "desc"}
      return = {type: "list"}
    } as $pesquisas_iniciadas

    db.query pergunta_clima {
      sort = {pergunta_clima.ordem: "asc"}
      return = {type: "list"}
    } as $todas_perguntas

    db.query resposta_clima_participacao {
      where = $db.resposta_clima_participacao.colaborador_id == $colaborador_autenticado.id
      return = {type: "list"}
      output = ["pergunta_clima_id"]
    } as $minhas_participacoes

    // Perguntas ja respondidas, como texto (",3,7,"): contains em texto e confiavel.
    var $respondidas_texto {
      value = ","
    }

    foreach ($minhas_participacoes) {
      each as $participacao {
        var.update $respondidas_texto {
          value = $respondidas_texto ~ ($participacao.pergunta_clima_id|to_text) ~ ","
        }
      }
    }

    var $pesquisas {
      value = []
    }

    foreach ($pesquisas_iniciadas) {
      each as $pesquisa {
        var $aberta {
          value = (($pesquisa.ativo == true) && ($pesquisa.data_fim >= $hoje))
        }

        var $perguntas_faltando {
          value = []
        }

        var $total_perguntas {
          value = 0
        }

        var $total_respondidas {
          value = 0
        }

        foreach ($todas_perguntas) {
          each as $pergunta {
            conditional {
              if ($pergunta.pesquisa_clima_id == $pesquisa.id) {
                var.update $total_perguntas {
                  value = $total_perguntas + 1
                }

                // Agulha numa variavel: o Xano tira os parenteses do argumento do filtro.
                var $agulha {
                  value = "," ~ ($pergunta.id|to_text) ~ ","
                }

                conditional {
                  if ($respondidas_texto|contains:$agulha) {
                    var.update $total_respondidas {
                      value = $total_respondidas + 1
                    }
                  }

                  else {
                    var.update $perguntas_faltando {
                      value = $perguntas_faltando|push:{id: $pergunta.id, texto: $pergunta.texto, ordem: $pergunta.ordem, escala: $pergunta.escala}
                    }
                  }
                }
              }
            }
          }
        }

        var.update $pesquisas {
          value = $pesquisas|push:{
            id               : $pesquisa.id
            titulo           : $pesquisa.titulo
            descricao        : $pesquisa.descricao
            data_inicio      : $pesquisa.data_inicio
            data_fim         : $pesquisa.data_fim
            minimo_respostas : $pesquisa.minimo_respostas
            aberta           : $aberta
            total_perguntas  : $total_perguntas
            respondidas      : $total_respondidas
            respondida       : (($total_perguntas > 0) && ($total_respondidas >= $total_perguntas))
            perguntas        : ($aberta ? $perguntas_faltando : [])
          }
        }
      }
    }
  }

  response = {
    sucesso  : true
    hoje     : $hoje
    pesquisas: $pesquisas
  }

  guid = "conectahr-minhas-pesquisas-clima-get-0001"
}
