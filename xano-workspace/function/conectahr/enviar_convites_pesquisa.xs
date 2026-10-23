// Convites de pesquisa (change notificacoes-de-publicacao, D3): avisa o publico, uma vez so, quando uma pesquisa
// fica respondivel, e no ciclo de 10 dias do termometro de humor. O convite e igual para todos e nao guarda nada
// sobre a resposta: ler ou abrir o aviso nao cria participacao, e nenhuma consulta liga o aviso a resposta.
// - Pesquisa de clima e avaliacao psicossocial da NR-1 (mesma tabela): ativa, no periodo, com perguntas e ainda
//   sem convite (convite_enviado_em); grava convite_enviado_em ao enviar.
// - Termometro de humor: um convite por ciclo (ciclo 0 = 21/10/2026), marcado em humor_convite.
// Roda na rotina diaria e na leitura do Inicio (humor GET), porque o plano nao tem tarefa agendada: o primeiro
// acesso do dia em que a pesquisa abre ja dispara. Marca antes de avisar, para nao repetir.
// Com aplicar = false so conta o que enviaria (status_operacional). Devolve {pesquisas, termometro}.
function "ConectaHR/enviar_convites_pesquisa" {
  input {
    bool aplicar
    int? autor_user_id?
    bool incluir_termometro
  }

  stack {
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $n_pesquisas {
      value = 0
    }

    var $n_termometro {
      value = 0
    }

    db.query pesquisa_clima {
      where = $db.pesquisa_clima.ativo == true && $db.pesquisa_clima.convite_enviado_em == null && $db.pesquisa_clima.data_inicio <= $hoje && $db.pesquisa_clima.data_fim >= $hoje
      return = {type: "list"}
    } as $abertas

    foreach ($abertas) {
      each as $p {
        db.query pergunta_clima {
          where = $db.pergunta_clima.pesquisa_clima_id == $p.id
          return = {type: "count"}
        } as $qtd_perguntas

        conditional {
          if ($qtd_perguntas > 0) {
            var.update $n_pesquisas {
              value = $n_pesquisas + 1
            }

            conditional {
              if ($input.aplicar) {
                // Marca antes de avisar: uma segunda leitura ao mesmo tempo ja nao acha a pesquisa pendente.
                db.edit pesquisa_clima {
                  field_name = "id"
                  field_value = $p.id
                  data = {
                    convite_enviado_em: "now"
                  }
                } as $pesquisa_convidada

                var $prefixo {
                  value = ($p.tipo == "psicossocial") ? "Nova avaliação de riscos psicossociais: " : "Nova pesquisa: "
                }

                var $titulo_convite {
                  value = ($prefixo ~ $p.titulo)|substr:0:150
                }

                var $mensagem_convite {
                  value = "Responda até " ~ ($p.data_fim|format_timestamp:"d/m":"UTC") ~ ". É anônima: ninguém vê a sua resposta."
                }

                function.run "ConectaHR/notificar_publico" {
                  input = {publico: "todos", departamento_ids: null, autor_user_id: $input.autor_user_id, tipo: "pesquisa_nova", assunto: "pesquisas", titulo: $titulo_convite, mensagem: $mensagem_convite, recurso: "pesquisa_clima", registro_id: $p.id}
                } as $convidados

              }
            }
          }
        }
      }
    }

    conditional {
      if ($input.incluir_termometro) {
        // Ciclo de hoje, como em humor GET: dia juliano da data de Sao Paulo; ciclo 0 = 21/10/2026 (2461335).
        var $ano {
          value = ($hoje|substr:0:4)|to_int
        }

        var $mes {
          value = ($hoje|substr:5:2)|to_int
        }

        var $dia {
          value = ($hoje|substr:8:2)|to_int
        }

        var $a_jd {
          value = ((14 - $mes) / 12)|floor
        }

        var $y_jd {
          value = $ano + 4800 - $a_jd
        }

        var $m_jd {
          value = $mes + (12 * $a_jd) - 3
        }

        var $parte_mes {
          value = (((153 * $m_jd) + 2) / 5)|floor
        }

        var $bissextos {
          value = (($y_jd / 4)|floor) - (($y_jd / 100)|floor) + (($y_jd / 400)|floor)
        }

        var $dia_juliano {
          value = $dia + $parte_mes + (365 * $y_jd) + $bissextos - 32045
        }

        var $ciclo {
          value = (($dia_juliano - 2461335) / 10)|floor
        }

        db.query humor_convite {
          where = $db.humor_convite.ciclo == $ciclo
          return = {type: "single"}
        } as $convite_ciclo

        conditional {
          if (($ciclo >= 0) && ($convite_ciclo == null)) {
            var.update $n_termometro {
              value = 1
            }

            conditional {
              if ($input.aplicar) {
                // Marca o ciclo antes de avisar (a chave unica barra um segundo convite do mesmo ciclo).
                db.add humor_convite {
                  data = {
                    ciclo     : $ciclo
                    quantidade: 0
                  }
                } as $convite_humor

                function.run "ConectaHR/notificar_publico" {
                  input = {publico: "todos", departamento_ids: null, autor_user_id: $input.autor_user_id, tipo: "pesquisa_nova", assunto: "pesquisas", titulo: "Termômetro de humor: como você está se sentindo?", mensagem: "Uma pergunta anônima, a cada 10 dias. Responda no Início.", recurso: "humor", registro_id: $ciclo}
                } as $convidados_humor

                db.edit humor_convite {
                  field_name = "id"
                  field_value = $convite_humor.id
                  data = {
                    quantidade: $convidados_humor
                  }
                } as $convite_humor_contado
              }
            }
          }
        }
      }
    }
  }

  response = {pesquisas: $n_pesquisas, termometro: $n_termometro}

  tags = ["conectahr"]
  guid = "conectahr-enviar-convites-pesquisa-0001"
}
