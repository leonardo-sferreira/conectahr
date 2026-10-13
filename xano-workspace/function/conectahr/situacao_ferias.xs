// Situacao de ferias de um colaborador numa data (change ponto-rep-p-e-ferias-clt, D9; tarefas 6.1 e 6.2). Usada por
// ferias/solicitacoes (com a data de inicio pedida) e por minha_situacao_ferias (com hoje + antecedencia), para as
// duas contarem igual.
//
// Periodo aquisitivo: comeca na admissao e renova a cada aniversario. As ferias de um aquisitivo sao tiradas no
// periodo concessivo seguinte (os 12 meses depois dele), entao a "janela" da data e do ultimo aniversario ate o
// proximo. Direito: dias_ferias_recesso (30). Antes do primeiro aniversario so ha direito se a regra for
// proporcional (ferias antecipadas, recesso do estagio): dias_ferias_recesso * dias de casa / 365.
// Saldo: direito menos os dias de ferias e os vendidos (abono) dos pedidos Pendente e Aprovada que comecam na janela.
// Datas comparadas como texto "Y-m-d" (aniversario de 29/02 vira 29/02 do ano, so usado como limite de texto).
function "ConectaHR/situacao_ferias" {
  input {
    int colaborador_id
    text data_referencia filters=trim
    int? ignorar_ferias_id?
  }

  stack {
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colab

    precondition ($colab != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colab.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra

    var $admissao {
      value = ($colab.data_admissao != null ? ($colab.data_admissao|to_timestamp|format_timestamp:"Y-m-d":"UTC") : null)
    }

    var $referencia {
      value = $input.data_referencia|substr:0:10
    }

    var $anos_completos {
      value = -1
    }

    var $ano_admissao {
      value = 0
    }

    var $mes_dia_admissao {
      value = ""
    }

    conditional {
      if ($admissao != null) {
        var.update $ano_admissao {
          value = ($admissao|substr:0:4)|to_int
        }

        var.update $mes_dia_admissao {
          value = $admissao|substr:5:5
        }

        var $ano_referencia {
          value = ($referencia|substr:0:4)|to_int
        }

        var $mes_dia_referencia {
          value = $referencia|substr:5:5
        }

        var.update $anos_completos {
          value = ($referencia < $admissao ? -1 : (($ano_referencia - $ano_admissao) - ($mes_dia_referencia < $mes_dia_admissao ? 1 : 0)))
        }
      }
    }

    var $direito_integral {
      value = ((($regra != null) && ($regra.dias_ferias_recesso != null)) ? $regra.dias_ferias_recesso : 30)
    }

    var $proporcional {
      value = (($regra != null) && ($regra.proporcional == true))
    }

    // Janela (periodo concessivo) e direito.
    var $janela_inicio {
      value = null
    }

    var $janela_fim {
      value = null
    }

    var $direito {
      value = 0
    }

    conditional {
      if ($anos_completos >= 1) {
        var.update $janela_inicio {
          value = (($ano_admissao + $anos_completos)|to_text) ~ "-" ~ $mes_dia_admissao
        }

        var.update $janela_fim {
          value = (($ano_admissao + $anos_completos + 1)|to_text) ~ "-" ~ $mes_dia_admissao
        }

        var.update $direito {
          value = $direito_integral
        }
      }

      elseif ($anos_completos == 0) {
        var.update $janela_inicio {
          value = $admissao
        }

        var.update $janela_fim {
          value = (($ano_admissao + 1)|to_text) ~ "-" ~ $mes_dia_admissao
        }

        conditional {
          if ($proporcional) {
            var $dias_de_casa {
              value = (((($referencia|to_timestamp) - ($admissao|to_timestamp)) / 86400000)|to_int)
            }

            var.update $direito {
              value = ((($direito_integral * $dias_de_casa) / 365)|floor)
            }
          }
        }
      }
    }

    // Pedidos da janela (pendentes e aprovados).
    db.query ferias {
      where = $db.ferias.colaborador_id == $colab.id
      sort = {ferias.data_inicio: "asc"}
      return = {type: "list"}
    } as $todas

    var $periodos {
      value = []
    }

    var $dias_usados {
      value = 0
    }

    var $dias_vendidos {
      value = 0
    }

    var $tem_periodo_14 {
      value = false
    }

    var $minimo_principal {
      value = ($regra != null ? $regra.minimo_periodo_principal : null)
    }

    foreach ($todas) {
      each as $f {
        var $inicio_f {
          value = ($f.data_inicio != null ? ($f.data_inicio|to_timestamp|format_timestamp:"Y-m-d":"UTC") : "")
        }

        var $conta {
          value = ((($f.status == "Pendente") || ($f.status == "Aprovada")) && ($janela_inicio != null) && ($inicio_f >= $janela_inicio) && ($inicio_f < $janela_fim) && ($f.id != $input.ignorar_ferias_id))
        }

        conditional {
          if ($conta) {
            var.update $periodos {
              value = $periodos|push:{id: $f.id, data_inicio: $inicio_f, data_fim: ($f.data_fim|to_timestamp|format_timestamp:"Y-m-d":"UTC"), quantidade_dias: $f.quantidade_dias, dias_abono: ($f.dias_abono != null ? $f.dias_abono : 0), status: $f.status}
            }

            var.update $dias_usados {
              value = $dias_usados + $f.quantidade_dias
            }

            var.update $dias_vendidos {
              value = $dias_vendidos + ($f.dias_abono != null ? $f.dias_abono : 0)
            }

            conditional {
              if (($minimo_principal != null) && ($f.quantidade_dias >= $minimo_principal)) {
                var.update $tem_periodo_14 {
                  value = true
                }
              }
            }
          }
        }
      }
    }

    var $saldo {
      value = $direito - $dias_usados - $dias_vendidos
    }

    conditional {
      if ($saldo < 0) {
        var.update $saldo {
          value = 0
        }
      }
    }

    var $minimo_outros {
      value = ((($regra != null) && ($regra.minimo_outros_periodos != null)) ? $regra.minimo_outros_periodos : 1)
    }

    var $maximo_abono {
      value = ((($regra != null) && ($regra.maximo_abono != null)) ? $regra.maximo_abono : 0)
    }

    var $maximo_periodos {
      value = ((($regra != null) && ($regra.maximo_periodos != null)) ? $regra.maximo_periodos : 1)
    }

    var $periodos_usados {
      value = ($periodos|count)
    }

    // Minimo do proximo periodo: o principal (14) enquanto nenhum periodo de 14 tiver sido pedido.
    var $minimo_proximo {
      value = ((($minimo_principal != null) && ($tem_periodo_14 == false)) ? $minimo_principal : $minimo_outros)
    }
  }

  response = {
    regra_id               : ($regra != null ? $regra.id : null)
    permite_solicitacao    : (($regra == null) || ($regra.permite_solicitacao_ferias != false))
    permite_fracionamento  : (($regra != null) && ($regra.permite_fracionamento == true))
    proporcional           : $proporcional
    antecedencia_minima    : ($regra != null ? $regra.antecedencia_ferias : null)
    anos_completos         : $anos_completos
    janela_inicio          : $janela_inicio
    janela_fim             : $janela_fim
    direito                : $direito
    dias_usados            : $dias_usados
    dias_vendidos          : $dias_vendidos
    saldo                  : $saldo
    periodos               : $periodos
    periodos_usados        : $periodos_usados
    maximo_periodos        : $maximo_periodos
    periodos_restantes     : ($maximo_periodos - $periodos_usados)
    tem_periodo_14         : $tem_periodo_14
    minimo_principal       : $minimo_principal
    minimo_outros          : $minimo_outros
    minimo_proximo         : $minimo_proximo
    maximo_abono           : $maximo_abono
    pode_vender            : (($maximo_abono > 0) && ($dias_vendidos == 0))
  }

  tags = ["conectahr"]
  guid = "conectahr-situacao-ferias-0001"
}
