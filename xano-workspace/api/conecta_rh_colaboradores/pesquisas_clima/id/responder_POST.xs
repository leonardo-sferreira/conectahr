// Envia as respostas de uma pesquisa de clima de uma vez (change pesquisa-clima-e-avaliacao-360, D2),
// em vez de uma chamada por pergunta. `respostas` = lista de {pergunta_id, nota}; precisa trazer todas as
// perguntas que a pessoa ainda nao respondeu, com a nota na escala de cada uma (concordancia 1 a 5, nps 0 a 10).
// Como em `perguntas_clima/{id}/responder`, a nota so soma no contador anonimo de `resposta_clima_agregado`;
// `resposta_clima_participacao` so impede responder duas vezes. O comentario opcional vai para
// `comentario_clima`, sem pessoa, departamento nem data. So pesquisa ativa e dentro do periodo.
query "pesquisas_clima/{id}/responder" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    json respostas
    text? comentario? filters=trim|max:1000
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

    precondition ($colaborador_autenticado.status != "Desligado") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode responder pesquisas."
    }

    db.get pesquisa_clima {
      field_name = "id"
      field_value = $input.id
    } as $pesquisa

    precondition ($pesquisa != null) {
      error_type = "notfound"
      error = "Pesquisa de clima nao encontrada."
    }

    precondition ($pesquisa.ativo) {
      error_type = "inputerror"
      error = "Esta pesquisa nao esta aberta para respostas."
    }

    precondition (($pesquisa.data_inicio <= $hoje) && ($pesquisa.data_fim >= $hoje)) {
      error_type = "inputerror"
      error = "Esta pesquisa esta fora do periodo de respostas."
    }

    db.query pergunta_clima {
      where = $db.pergunta_clima.pesquisa_clima_id == $pesquisa.id
      sort = {pergunta_clima.ordem: "asc"}
      return = {type: "list"}
    } as $perguntas

    precondition (($perguntas|count) > 0) {
      error_type = "inputerror"
      error = "Esta pesquisa ainda nao tem perguntas."
    }

    db.query resposta_clima_participacao {
      where = $db.resposta_clima_participacao.colaborador_id == $colaborador_autenticado.id
      return = {type: "list"}
      output = ["pergunta_clima_id"]
    } as $minhas_participacoes

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

    // 1) Confere tudo antes de gravar qualquer coisa: cada pergunta que falta precisa de uma nota valida.
    var $a_gravar {
      value = []
    }

    foreach ($perguntas) {
      each as $pergunta {
        // Agulha numa variavel: o Xano tira os parenteses do argumento do filtro.
        var $agulha {
          value = "," ~ ($pergunta.id|to_text) ~ ","
        }

        conditional {
          if (($respondidas_texto|contains:$agulha) == false) {
            // Nota como texto: "!= null" trata 0 como nulo nesta plataforma, e 0 e uma nota valida no nps.
            var $nota_texto {
              value = ""
            }

            foreach ($input.respostas) {
              each as $resposta {
                conditional {
                  if ((($resposta|get:"pergunta_id")|to_text) == ($pergunta.id|to_text)) {
                    var.update $nota_texto {
                      value = (($resposta|get:"nota")|to_text)
                    }
                  }
                }
              }
            }

            precondition ($nota_texto != "") {
              error_type = "inputerror"
              error = "Responda todas as perguntas antes de enviar."
            }

            var $nota {
              value = $nota_texto|to_int
            }

            var $nota_maxima {
              value = ($pergunta.escala == "nps" ? 10 : 5)
            }

            var $nota_minima {
              value = ($pergunta.escala == "nps" ? 0 : 1)
            }

            precondition (($nota >= $nota_minima) && ($nota <= $nota_maxima)) {
              error_type = "inputerror"
              error = "Nota fora da escala da pergunta."
            }

            var.update $a_gravar {
              value = $a_gravar|push:{pergunta_id: $pergunta.id, nota: $nota}
            }
          }
        }
      }
    }

    precondition (($a_gravar|count) > 0) {
      error_type = "inputerror"
      error = "Voce ja respondeu esta pesquisa."
    }

    // 0 = sem departamento (ver resposta_clima_agregado.xs).
    var $departamento_agregado {
      value = ($colaborador_autenticado.departamento_id == null ? 0 : $colaborador_autenticado.departamento_id)
    }

    var $comentario {
      value = (($input.comentario == null) ? "" : $input.comentario)
    }

    // 2) Grava: soma nos contadores anonimos e marca a participacao, tudo ou nada.
    db.transaction {
      stack {
        foreach ($a_gravar) {
          each as $item {
            db.query resposta_clima_agregado {
              where = $db.resposta_clima_agregado.pergunta_clima_id == $item.pergunta_id && $db.resposta_clima_agregado.departamento_id == $departamento_agregado && $db.resposta_clima_agregado.nota == $item.nota
              return = {type: "single"}
            } as $contador_existente

            conditional {
              if ($contador_existente == null) {
                db.add resposta_clima_agregado {
                  data = {
                    pergunta_clima_id: $item.pergunta_id
                    departamento_id  : $departamento_agregado
                    nota             : $item.nota
                    quantidade       : 1
                  }
                } as $contador_criado
              }

              else {
                db.edit resposta_clima_agregado {
                  field_name = "id"
                  field_value = $contador_existente.id
                  data = {quantidade: $contador_existente.quantidade + 1}
                } as $contador_atualizado
              }
            }

            db.add resposta_clima_participacao {
              data = {
                pergunta_clima_id: $item.pergunta_id
                colaborador_id   : $colaborador_autenticado.id
              }
            } as $participacao_criada
          }
        }

        conditional {
          if ($comentario != "") {
            db.add comentario_clima {
              data = {
                pesquisa_clima_id: $pesquisa.id
                texto            : $comentario
              }
            } as $comentario_criado
          }
        }
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Respostas registradas. Obrigado por participar."
  }

  guid = "conectahr-pesquisas-clima-responder-lote-post-0001"
}
