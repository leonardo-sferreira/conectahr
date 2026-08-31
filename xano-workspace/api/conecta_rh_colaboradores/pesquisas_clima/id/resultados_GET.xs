// RH/ADMIN consulta os resultados agrupados por departamento (e o
// geral da empresa) de cada pergunta da pesquisa. Um grupo (ou o geral)
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

    db.query pergunta_clima {
      where = $db.pergunta_clima.pesquisa_clima_id == $pesquisa.id
      sort = {pergunta_clima.ordem: "asc"}
      return = {type: "list"}
    } as $perguntas_da_pesquisa

    db.query departamento {
      where = $db.departamento.ativo == true
      return = {type: "list"}
    } as $departamentos

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
        foreach ($departamentos) {
          each as $departamento_item {
            db.query resposta_clima {
              where = $db.resposta_clima.pergunta_clima_id == $pergunta_item.id && $db.resposta_clima.departamento_id == $departamento_item.id
              return = {type: "list"}
            } as $respostas_grupo

            var.update $contagem_temp {
              value = ($respostas_grupo|count)
            }

            var.update $soma_temp {
              value = 0
            }

            foreach ($respostas_grupo) {
              each as $resposta_item {
                var.update $soma_temp {
                  value = $soma_temp + $resposta_item.nota
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
            }
          }
        }

        db.query resposta_clima {
          where = $db.resposta_clima.pergunta_clima_id == $pergunta_item.id
          return = {type: "list"}
        } as $respostas_geral_pergunta

        var.update $contagem_temp {
          value = ($respostas_geral_pergunta|count)
        }

        var.update $soma_temp {
          value = 0
        }

        foreach ($respostas_geral_pergunta) {
          each as $resposta_geral_item {
            var.update $soma_temp {
              value = $soma_temp + $resposta_geral_item.nota
            }
          }
        }

        conditional {
          if ($contagem_temp >= $pesquisa.minimo_respostas) {
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
