// Regras de um pedido de ferias (change ponto-rep-p-e-ferias-clt, tarefa 6.1; spec "Ferias pela CLT"). Recebe a
// situacao de ConectaHR/situacao_ferias (na data de inicio) e o pedido, e devolve a primeira regra que falha em `erro`
// (ou null) e o saldo que sobraria. ferias/solicitacoes chama esta funcao; separada para as regras serem testadas com
// situacoes simuladas. So le a tabela feriado. `hoje` (Y-m-d) e a data do pedido.
function "ConectaHR/validar_pedido_ferias" {
  input {
    json situacao
    text data_inicio filters=trim
    text data_fim filters=trim
    int quantidade_dias
    int? dias_abono?
    text hoje filters=trim
  }

  stack {
    var $s {
      value = $input.situacao
    }

    var $abono {
      value = ($input.dias_abono != null ? $input.dias_abono : 0)
    }

    var $inicio_ts {
      value = $input.data_inicio|to_timestamp
    }

    var $dias_nas_datas {
      value = (((($input.data_fim|to_timestamp) - $inicio_ts) / 86400000)|to_int) + 1
    }

    var $antecedencia {
      value = ((($inicio_ts - ($input.hoje|to_timestamp)) / 86400000)|to_int)
    }

    var $restante {
      value = $s.saldo - $input.quantidade_dias - $abono
    }

    var $dia_semana {
      value = $inicio_ts|format_timestamp:"N":"UTC"
    }

    var $um_dia_depois {
      value = $inicio_ts|add_secs_to_timestamp:86400|format_timestamp:"Y-m-d":"UTC"
    }

    var $dois_dias_depois {
      value = $inicio_ts|add_secs_to_timestamp:172800|format_timestamp:"Y-m-d":"UTC"
    }

    db.query feriado {
      where = $db.feriado.data >= $um_dia_depois && $db.feriado.data <= $dois_dias_depois && $db.feriado.ativo == true
      return = {type: "list"}
    } as $feriados_perto

    var $feriado_logo_depois {
      value = null
    }

    foreach ($feriados_perto) {
      each as $fp {
        conditional {
          if (($fp.tipo == null) || ($fp.tipo == "feriado")) {
            var.update $feriado_logo_depois {
              value = $fp.nome
            }
          }
        }
      }
    }

    // A primeira regra que falha, na ordem em que a pessoa resolveria.
    var $erro {
      value = null
    }

    conditional {
      if ($s.permite_solicitacao == false) {
        var.update $erro {
          value = "Solicitacao de ferias nao habilitada para o tipo de contrato deste colaborador."
        }
      }

      elseif ($input.data_fim < $input.data_inicio) {
        var.update $erro {
          value = "A data final deve ser igual ou posterior a data inicial."
        }
      }

      elseif ($dias_nas_datas != $input.quantidade_dias) {
        var.update $erro {
          value = "A quantidade de dias nao confere com as datas de inicio e fim."
        }
      }

      elseif (($s.antecedencia_minima != null) && ($antecedencia < $s.antecedencia_minima)) {
        var.update $erro {
          value = "Ferias precisam ser pedidas com pelo menos " ~ ($s.antecedencia_minima|to_text) ~ " dias de antecedencia."
        }
      }

      elseif (($s.anos_completos < 0) || (($s.anos_completos == 0) && ($s.proporcional == false))) {
        var.update $erro {
          value = "Voce ainda nao completou o periodo aquisitivo (12 meses de trabalho) para esta data."
        }
      }

      elseif ($abono > $s.maximo_abono) {
        var.update $erro {
          value = ($s.maximo_abono > 0 ? ("E possivel vender no maximo " ~ ($s.maximo_abono|to_text) ~ " dias.") : "Este tipo de contrato nao permite vender dias de ferias.")
        }
      }

      elseif (($abono > 0) && ($s.dias_vendidos > 0)) {
        var.update $erro {
          value = "A venda de dias ja foi feita neste periodo aquisitivo."
        }
      }

      elseif ($s.periodos_usados >= $s.maximo_periodos) {
        var.update $erro {
          value = "Voce ja pediu o numero maximo de periodos de ferias deste periodo aquisitivo."
        }
      }

      elseif (($s.periodos_usados > 0) && ($s.permite_fracionamento == false)) {
        var.update $erro {
          value = "Este tipo de contrato nao permite dividir as ferias."
        }
      }

      elseif ($input.quantidade_dias < $s.minimo_outros) {
        var.update $erro {
          value = "Cada periodo de ferias precisa ter pelo menos " ~ ($s.minimo_outros|to_text) ~ " dias."
        }
      }

      elseif (($input.quantidade_dias + $abono) > $s.saldo) {
        var.update $erro {
          value = "Saldo insuficiente: restam " ~ ($s.saldo|to_text) ~ " dias neste periodo aquisitivo."
        }
      }

      elseif (($restante > 0) && ($restante < $s.minimo_outros)) {
        var.update $erro {
          value = "Sobrariam " ~ ($restante|to_text) ~ " dias, menos do que um periodo permite (" ~ ($s.minimo_outros|to_text) ~ "). Peca todo o saldo ou deixe pelo menos " ~ ($s.minimo_outros|to_text) ~ " dias."
        }
      }

      elseif (($restante > 0) && (($s.periodos_usados + 1) >= $s.maximo_periodos)) {
        var.update $erro {
          value = "Sobrariam " ~ ($restante|to_text) ~ " dias, mas este ja seria o ultimo periodo permitido. Peca todo o saldo."
        }
      }

      elseif (($s.minimo_principal != null) && ($s.tem_periodo_14 == false) && ($input.quantidade_dias < $s.minimo_principal) && ($restante < $s.minimo_principal)) {
        var.update $erro {
          value = "Um dos periodos precisa ter pelo menos " ~ ($s.minimo_principal|to_text) ~ " dias, e o saldo que sobraria nao comporta. Aumente este periodo."
        }
      }

      elseif (($dia_semana == "5") || ($dia_semana == "6") || ($feriado_logo_depois != null)) {
        var.update $erro {
          value = "As ferias nao podem comecar nos dois dias antes de um feriado ou do descanso semanal (sexta e sabado). Escolha outro dia de inicio."
        }
      }
    }
  }

  response = {
    erro          : $erro
    saldo_restante: $restante
  }

  tags = ["conectahr"]
  guid = "conectahr-validar-pedido-ferias-0001"
}
