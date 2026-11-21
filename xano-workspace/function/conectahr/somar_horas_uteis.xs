// Soma horas uteis a um instante (change sla-de-solicitacoes, D2). Dia util: segunda a sexta, menos os
// feriados nacionais ativos da tabela `feriado` (sem estado e sem municipio; ponto facultativo nao conta).
// O dia util vale 24 horas, no fuso America/Sao_Paulo.
// 1. Inicio em dia nao util passa para 00:00 do proximo dia util.
// 2. Soma floor(horas / 24) dias uteis, de 24 em 24 horas, pulando os nao uteis.
// 3. Soma o resto em horas; se cair em dia nao util, anda de 24 em 24 horas ate um dia util.
// Ate 720 horas (30 dias uteis); os lacos andam no maximo 60 dias de calendario.
function "ConectaHR/somar_horas_uteis" {
  input {
    timestamp inicio
    int horas
  }

  stack {
    db.query feriado {
      where = $db.feriado.ativo == true && $db.feriado.abrangencia == "nacional"
      return = {type: "list"}
      output = ["data", "tipo", "estado", "municipio"]
    } as $feriados_todos

    var $feriados_texto {
      value = ","
    }

    foreach ($feriados_todos) {
      each as $f {
        conditional {
          if (($f.tipo != "ponto_facultativo") && (($f.estado == null) || ($f.estado == "")) && (($f.municipio == null) || ($f.municipio == ""))) {
            var.update $feriados_texto {
              value = $feriados_texto ~ ($f.data|to_text) ~ ","
            }
          }
        }
      }
    }

    var $passos {
      value = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60"|split:","
    }

    var $horas_total {
      value = ($input.horas < 1) ? 1 : (($input.horas > 720) ? 720 : $input.horas)
    }

    var $atual {
      value = $input.inicio
    }

    // 1. Inicio em dia nao util: 00:00 do proximo dia util.
    var $dia_semana {
      value = $atual|format_timestamp:"N":"America/Sao_Paulo"|to_int
    }

    var $data_local {
      value = $atual|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    conditional {
      if (($dia_semana >= 6) || ($feriados_texto|contains:("," ~ $data_local ~ ","))) {
        var.update $atual {
          value = ($data_local ~ " 00:00:00")|to_timestamp:"America/Sao_Paulo"
        }

        var $achou_inicio {
          value = false
        }

        foreach ($passos) {
          each as $p1 {
            conditional {
              if ($achou_inicio == false) {
                var.update $atual {
                  value = $atual|add_secs_to_timestamp:86400
                }

                var $ds1 {
                  value = $atual|format_timestamp:"N":"America/Sao_Paulo"|to_int
                }

                var $dl1 {
                  value = $atual|format_timestamp:"Y-m-d":"America/Sao_Paulo"
                }

                conditional {
                  if (($ds1 <= 5) && (($feriados_texto|contains:("," ~ $dl1 ~ ",")) == false)) {
                    var.update $achou_inicio {
                      value = true
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    // 2. Dias uteis inteiros.
    var $dias_restantes {
      value = ($horas_total / 24)|floor
    }

    foreach ($passos) {
      each as $p2 {
        conditional {
          if ($dias_restantes > 0) {
            var.update $atual {
              value = $atual|add_secs_to_timestamp:86400
            }

            var $ds2 {
              value = $atual|format_timestamp:"N":"America/Sao_Paulo"|to_int
            }

            var $dl2 {
              value = $atual|format_timestamp:"Y-m-d":"America/Sao_Paulo"
            }

            conditional {
              if (($ds2 <= 5) && (($feriados_texto|contains:("," ~ $dl2 ~ ",")) == false)) {
                var.update $dias_restantes {
                  value = $dias_restantes - 1
                }
              }
            }
          }
        }
      }
    }

    // 3. O resto em horas; se cair em dia nao util, anda ate um dia util mantendo o horario.
    var $resto_horas {
      value = $horas_total - (($horas_total / 24)|floor) * 24
    }

    var.update $atual {
      value = $atual|add_secs_to_timestamp:($resto_horas * 3600)
    }

    var $no_util {
      value = false
    }

    foreach ($passos) {
      each as $p3 {
        conditional {
          if ($no_util == false) {
            var $ds3 {
              value = $atual|format_timestamp:"N":"America/Sao_Paulo"|to_int
            }

            var $dl3 {
              value = $atual|format_timestamp:"Y-m-d":"America/Sao_Paulo"
            }

            conditional {
              if (($ds3 <= 5) && (($feriados_texto|contains:("," ~ $dl3 ~ ",")) == false)) {
                var.update $no_util {
                  value = true
                }
              }

              else {
                var.update $atual {
                  value = $atual|add_secs_to_timestamp:86400
                }
              }
            }
          }
        }
      }
    }
  }

  response = $atual

  tags = ["conectahr"]
  guid = "conectahr-somar-horas-uteis-0001"
}
