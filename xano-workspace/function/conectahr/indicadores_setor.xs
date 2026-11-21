// Indicadores agregados de um setor (change backend-gestor-pendencias, D2), sem nomes nem ids de pessoas: os ultimos
// 6 meses (horas extras, ausencias e absenteismo), o saldo atual do banco de horas e o clima da ultima pesquisa de
// clima encerrada. Setor com menos de `minimo` pessoas (os endpoints passam 5) volta sem numeros, com o motivo.
// Absenteismo: dias uteis cobertos por ausencia Aprovada ou Registrado / (pessoas x dias uteis do mes), em %; dia util
// e segunda a sexta, sem os feriados nacionais ativos (ponto facultativo nao conta). Clima: % de respostas 4 e 5 das
// perguntas de concordancia, so com o minimo de respostas da pesquisa no setor.
function "ConectaHR/indicadores_setor" {
  input {
    int departamento_id
    int? excluir_colaborador_id?
    int? minimo?
  }

  stack {
    var $minimo_pessoas {
      value = ($input.minimo == null) ? 5 : $input.minimo
    }

    db.get departamento {
      field_name = "id"
      field_value = $input.departamento_id
      output = ["id", "nome"]
    } as $setor

    db.query colaborador {
      where = $db.colaborador.departamento_id == $input.departamento_id && $db.colaborador.anonimizado_em == null
      return = {type: "list"}
      output = ["id", "status"]
    } as $fichas_setor

    var $ids_texto {
      value = ","
    }

    var $pessoas {
      value = 0
    }

    foreach ($fichas_setor) {
      each as $f {
        conditional {
          if (($f.status != "Desligado") && (($input.excluir_colaborador_id == null) || ($f.id != $input.excluir_colaborador_id))) {
            var.update $ids_texto {
              value = $ids_texto ~ ($f.id|to_text) ~ ","
            }

            var.update $pessoas {
              value = $pessoas + 1
            }
          }
        }
      }
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $meses {
      value = []
    }

    var $banco_horas {
      value = null
    }

    var $clima {
      value = null
    }

    var $motivo {
      value = null
    }

    conditional {
      if ($pessoas < $minimo_pessoas) {
        var.update $motivo {
          value = "O setor tem menos de " ~ ($minimo_pessoas|to_text) ~ " pessoas: os números ficam ocultos para não identificar ninguém."
        }
      }

      else {
        // Feriados nacionais (texto ",Y-m-d," para o contains).
        db.query feriado {
          where = $db.feriado.ativo == true && $db.feriado.abrangencia == "nacional"
          return = {type: "list"}
          output = ["data", "tipo", "estado", "municipio"]
        } as $feriados_todos

        var $feriados_texto {
          value = ","
        }

        foreach ($feriados_todos) {
          each as $fe {
            conditional {
              if (($fe.tipo != "ponto_facultativo") && (($fe.estado == null) || ($fe.estado == "")) && (($fe.municipio == null) || ($fe.municipio == ""))) {
                var.update $feriados_texto {
                  value = $feriados_texto ~ ($fe.data|to_text) ~ ","
                }
              }
            }
          }
        }

        var $passos {
          value = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"|split:","
        }

        var $ano_atual {
          value = ($hoje|substr:0:4)|to_int
        }

        var $mes_atual {
          value = ($hoje|substr:5:2)|to_int
        }

        // Os 6 meses, do mais antigo ao atual.
        var $deslocamentos {
          value = "5,4,3,2,1,0"|split:","
        }

        var $inicio_periodo {
          value = null
        }

        foreach ($deslocamentos) {
          each as $k_txt {
            var $k {
              value = $k_txt|to_int
            }

            var $m {
              value = $mes_atual - $k
            }

            var $a {
              value = $ano_atual
            }

            conditional {
              if ($m <= 0) {
                var.update $m {
                  value = $m + 12
                }

                var.update $a {
                  value = $a - 1
                }
              }
            }

            var $chave {
              value = ($a|to_text) ~ "-" ~ (($m < 10) ? ("0" ~ ($m|to_text)) : ($m|to_text))
            }

            var $proximo_m {
              value = ($m == 12) ? 1 : ($m + 1)
            }

            var $proximo_a {
              value = ($m == 12) ? ($a + 1) : $a
            }

            var $proximo_inicio {
              value = ($proximo_a|to_text) ~ "-" ~ (($proximo_m < 10) ? ("0" ~ ($proximo_m|to_text)) : ($proximo_m|to_text)) ~ "-01"
            }

            var $ultimo_dia {
              value = (($proximo_inicio ~ " 12:00:00")|to_timestamp:"America/Sao_Paulo")|add_secs_to_timestamp:-86400|format_timestamp:"Y-m-d":"America/Sao_Paulo"
            }

            var $fim_mes {
              value = ($k == 0) ? $hoje : $ultimo_dia
            }

            conditional {
              if ($inicio_periodo == null) {
                var.update $inicio_periodo {
                  value = $chave ~ "-01"
                }
              }
            }

            var.update $meses {
              value = $meses|push:{chave: $chave, inicio: ($chave ~ "-01"), fim: $fim_mes}
            }
          }
        }

        db.query registro_ponto {
          where = $db.registro_ponto.data >= $inicio_periodo && $db.registro_ponto.data <= $hoje
          return = {type: "list"}
          output = ["colaborador_id", "data", "horas_extras"]
        } as $registros

        db.query ausencia {
          where = $db.ausencia.data_fim >= $inicio_periodo && $db.ausencia.data_inicio <= $hoje
          return = {type: "list"}
          output = ["colaborador_id", "data_inicio", "data_fim", "status"]
        } as $ausencias_periodo

        // So as ausencias validas de quem e do setor.
        var $ausencias_setor {
          value = []
        }

        foreach ($ausencias_periodo) {
          each as $au {
            conditional {
              if ((($au.status == "Aprovada") || ($au.status == "Registrado")) && ($ids_texto|contains:("," ~ ($au.colaborador_id|to_text) ~ ","))) {
                var.update $ausencias_setor {
                  value = $ausencias_setor|push:$au
                }
              }
            }
          }
        }

        var $resultado_meses {
          value = []
        }

        foreach ($meses) {
          each as $mes_item {
            var $horas_extras {
              value = 0
            }

            foreach ($registros) {
              each as $rp {
                conditional {
                  if (($rp.horas_extras != null) && (($rp.data|to_text|substr:0:7) == $mes_item.chave) && ($ids_texto|contains:("," ~ ($rp.colaborador_id|to_text) ~ ","))) {
                    var.update $horas_extras {
                      value = $horas_extras + $rp.horas_extras
                    }
                  }
                }
              }
            }

            var $qtd_ausencias {
              value = 0
            }

            foreach ($ausencias_setor) {
              each as $as1 {
                conditional {
                  if ((($as1.data_inicio|to_text) <= $mes_item.fim) && (($as1.data_fim|to_text) >= $mes_item.inicio)) {
                    var.update $qtd_ausencias {
                      value = $qtd_ausencias + 1
                    }
                  }
                }
              }
            }

            var $dias_uteis {
              value = 0
            }

            var $dias_ausencia {
              value = 0
            }

            var $inicio_ts {
              value = ($mes_item.inicio ~ " 12:00:00")|to_timestamp:"America/Sao_Paulo"
            }

            foreach ($passos) {
              each as $p {
                var $dia {
                  value = $inicio_ts|add_secs_to_timestamp:((($p|to_int) - 1) * 86400)|format_timestamp:"Y-m-d":"America/Sao_Paulo"
                }

                var $dia_semana {
                  value = ($inicio_ts|add_secs_to_timestamp:((($p|to_int) - 1) * 86400)|format_timestamp:"N":"America/Sao_Paulo")|to_int
                }

                conditional {
                  if (($dia <= $mes_item.fim) && (($dia|substr:0:7) == $mes_item.chave) && ($dia_semana <= 5) && (($feriados_texto|contains:("," ~ $dia ~ ",")) == false)) {
                    var.update $dias_uteis {
                      value = $dias_uteis + 1
                    }

                    foreach ($ausencias_setor) {
                      each as $as2 {
                        conditional {
                          if ((($as2.data_inicio|to_text) <= $dia) && (($as2.data_fim|to_text) >= $dia)) {
                            var.update $dias_ausencia {
                              value = $dias_ausencia + 1
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }

            var $base {
              value = $pessoas * $dias_uteis
            }

            var $absenteismo {
              value = ($base > 0) ? ((($dias_ausencia * 1000) / $base)|round) / 10 : null
            }

            var.update $resultado_meses {
              value = $resultado_meses|push:{mes: $mes_item.chave, horas_extras: ($horas_extras * 100|round) / 100, ausencias: $qtd_ausencias, dias_uteis: $dias_uteis, dias_ausencia: $dias_ausencia, absenteismo: $absenteismo}
            }
          }
        }

        var.update $meses {
          value = $resultado_meses
        }

        // Banco de horas: saldo atual (creditos menos debitos) do setor.
        db.query banco_horas_lancamento {
          return = {type: "list"}
          output = ["colaborador_id", "tipo", "horas"]
        } as $lancamentos

        var $saldo {
          value = 0
        }

        foreach ($lancamentos) {
          each as $l {
            conditional {
              if ($ids_texto|contains:("," ~ ($l.colaborador_id|to_text) ~ ",")) {
                var.update $saldo {
                  value = ($l.tipo == "credito") ? ($saldo + $l.horas) : ($saldo - $l.horas)
                }
              }
            }
          }
        }

        var.update $banco_horas {
          value = ($saldo * 100|round) / 100
        }

        // Clima: a ultima pesquisa de clima encerrada (tipo clima; termina antes de hoje ou foi encerrada).
        db.query pesquisa_clima {
          sort = {pesquisa_clima.data_fim: "desc"}
          return = {type: "list"}
          output = ["id", "titulo", "data_fim", "ativo", "tipo", "minimo_respostas"]
        } as $pesquisas

        var $pesquisa_clima {
          value = null
        }

        foreach ($pesquisas) {
          each as $pq {
            conditional {
              if (($pesquisa_clima == null) && (($pq.tipo == null) || ($pq.tipo == "clima")) && (($pq.ativo == false) || (($pq.data_fim|to_text) < $hoje))) {
                var.update $pesquisa_clima {
                  value = $pq
                }
              }
            }
          }
        }

        conditional {
          if ($pesquisa_clima != null) {
            db.query pergunta_clima {
              where = $db.pergunta_clima.pesquisa_clima_id == $pesquisa_clima.id
              return = {type: "list"}
              output = ["id", "escala"]
            } as $perguntas

            var $perguntas_texto {
              value = ","
            }

            var $primeira_pergunta {
              value = null
            }

            foreach ($perguntas) {
              each as $pg {
                conditional {
                  if ($pg.escala == "concordancia") {
                    var.update $perguntas_texto {
                      value = $perguntas_texto ~ ($pg.id|to_text) ~ ","
                    }
                  }
                }

                conditional {
                  if ($primeira_pergunta == null) {
                    var.update $primeira_pergunta {
                      value = $pg.id
                    }
                  }
                }
              }
            }

            db.query resposta_clima_agregado {
              where = $db.resposta_clima_agregado.departamento_id == $input.departamento_id
              return = {type: "list"}
              output = ["pergunta_clima_id", "nota", "quantidade"]
            } as $agregados

            var $favoraveis {
              value = 0
            }

            var $respostas {
              value = 0
            }

            foreach ($agregados) {
              each as $ag {
                conditional {
                  if ($perguntas_texto|contains:("," ~ ($ag.pergunta_clima_id|to_text) ~ ",")) {
                    var.update $respostas {
                      value = $respostas + $ag.quantidade
                    }

                    conditional {
                      if ($ag.nota >= 4) {
                        var.update $favoraveis {
                          value = $favoraveis + $ag.quantidade
                        }
                      }
                    }
                  }
                }
              }
            }

            var $participantes {
              value = 0
            }

            conditional {
              if ($primeira_pergunta != null) {
                db.query resposta_clima_participacao {
                  where = $db.resposta_clima_participacao.pergunta_clima_id == $primeira_pergunta
                  return = {type: "list"}
                  output = ["colaborador_id"]
                } as $participacoes

                foreach ($participacoes) {
                  each as $pa {
                    conditional {
                      if ($ids_texto|contains:("," ~ ($pa.colaborador_id|to_text) ~ ",")) {
                        var.update $participantes {
                          value = $participantes + 1
                        }
                      }
                    }
                  }
                }
              }
            }

            var $minimo_clima {
              value = ($pesquisa_clima.minimo_respostas == null) ? 5 : $pesquisa_clima.minimo_respostas
            }

            var $favoravel_pct {
              value = (($participantes >= $minimo_clima) && ($respostas > 0)) ? (($favoraveis * 100 / $respostas)|round) : null
            }

            var.update $clima {
              value = {pesquisa: $pesquisa_clima.titulo, encerrada_em: $pesquisa_clima.data_fim, participantes: $participantes, minimo: $minimo_clima, favoravel_pct: $favoravel_pct}
            }
          }
        }
      }
    }

    var $nome_setor {
      value = ($setor != null) ? $setor.nome : null
    }
  }

  response = {setor: $nome_setor, pessoas: $pessoas, minimo: $minimo_pessoas, suprimido: ($motivo != null), motivo: $motivo, meses: $meses, banco_horas: $banco_horas, clima: $clima}

  tags = ["conectahr"]
  guid = "conectahr-indicadores-setor-0001"
}
