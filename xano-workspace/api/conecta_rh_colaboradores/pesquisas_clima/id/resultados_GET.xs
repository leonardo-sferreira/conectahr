// RH/ADMIN consulta os resultados agrupados por departamento (e o
// geral da empresa) de cada pergunta da pesquisa, somando os contadores
// anonimos de `resposta_clima_agregado`. Um grupo (ou o geral)
// so aparece quando a quantidade de respostas atinge o minimo
// configurado na pesquisa - abaixo disso, e omitido (nao ha como
// identificar quem respondeu, mas um grupo pequeno demais poderia
// permitir inferir a resposta de uma pessoa especifica por eliminacao).
query "pesquisas_clima/{id}/resultados" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar resultados de clima."
    }

    db.get pesquisa_clima {
      field_name = "id"
      field_value = $input.id
    } as $pesquisa

    precondition ($pesquisa != null) {
      error_type = "notfound"
      error = "Pesquisa de clima nao encontrada."
    }

    // Os resultados so abrem depois que a pesquisa esta encerrada (desligada ou
    // com o periodo vencido). Com a pesquisa aberta, dois pedidos em sequencia
    // revelariam a resposta de quem respondeu entre eles.
    var $hoje_resultados {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    var $pesquisa_encerrada {
      value = (($pesquisa.ativo == false) || ($pesquisa.data_fim < $hoje_resultados))
    }

    precondition ($pesquisa_encerrada) {
      error_type = "inputerror"
      error = "Os resultados so ficam disponiveis depois que a pesquisa for encerrada."
    }

    db.query pergunta_clima {
      where = $db.pergunta_clima.pesquisa_clima_id == $pesquisa.id
      sort = {pergunta_clima.ordem: "asc"}
      return = {type: "list"}
    } as $perguntas_da_pesquisa

    // Todos os departamentos (inclusive inativos): respostas de qualquer um deles
    // entram no total e, por isso, tambem contam na supressao complementar.
    db.query departamento {
      return = {type: "list"}
      output = ["id"]
    } as $departamentos_todos

    // Grupo 0 = colaborador sem departamento (ver resposta_clima_agregado.xs).
    var $departamentos {
      value = $departamentos_todos|push:{id: 0}
    }

    var $grupos_suprimidos {
      value = 0
    }

    var $resultados {
      value = []
    }

    var $soma_temp {
      value = 0
    }

    var $contagem_temp {
      value = 0
    }

    foreach ($perguntas_da_pesquisa) {
      each as $pergunta_item {
        var.update $grupos_suprimidos {
          value = 0
        }

        foreach ($departamentos) {
          each as $departamento_item {
            db.query resposta_clima_agregado {
              where = $db.resposta_clima_agregado.pergunta_clima_id == $pergunta_item.id && $db.resposta_clima_agregado.departamento_id == $departamento_item.id
              return = {type: "list"}
            } as $contadores_grupo

            var.update $contagem_temp {
              value = 0
            }

            var.update $soma_temp {
              value = 0
            }

            foreach ($contadores_grupo) {
              each as $contador_item {
                var.update $contagem_temp {
                  value = $contagem_temp + $contador_item.quantidade
                }

                var.update $soma_temp {
                  value = $soma_temp + ($contador_item.nota * $contador_item.quantidade)
                }
              }
            }

            conditional {
              if ($contagem_temp >= $pesquisa.minimo_respostas) {
                var.update $resultados {
                  value = $resultados|push:{
                    pergunta_id     : $pergunta_item.id
                    departamento_id : $departamento_item.id
                    quantidade      : $contagem_temp
                    media           : ($soma_temp / $contagem_temp)
                  }
                }
              }

              elseif ($contagem_temp > 0) {
                var.update $grupos_suprimidos {
                  value = $grupos_suprimidos + 1
                }
              }
            }
          }
        }

        db.query resposta_clima_agregado {
          where = $db.resposta_clima_agregado.pergunta_clima_id == $pergunta_item.id
          return = {type: "list"}
        } as $contadores_geral_pergunta

        var.update $contagem_temp {
          value = 0
        }

        var.update $soma_temp {
          value = 0
        }

        foreach ($contadores_geral_pergunta) {
          each as $contador_geral_item {
            var.update $contagem_temp {
              value = $contagem_temp + $contador_geral_item.quantidade
            }

            var.update $soma_temp {
              value = $soma_temp + ($contador_geral_item.nota * $contador_geral_item.quantidade)
            }
          }
        }

        // Supressao complementar: com um unico grupo omitido, o total menos os grupos
        // visiveis revelaria o grupo omitido, entao o total tambem e omitido.
        conditional {
          if ($contagem_temp >= $pesquisa.minimo_respostas && $grupos_suprimidos != 1) {
            var.update $resultados {
              value = $resultados|push:{
                pergunta_id     : $pergunta_item.id
                departamento_id : null
                quantidade      : $contagem_temp
                media           : ($soma_temp / $contagem_temp)
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso    : true
    minimo_respostas: $pesquisa.minimo_respostas
    resultados : $resultados
  }

  guid = "conectahr-pesquisas-clima-resultados-get-0001"
}
