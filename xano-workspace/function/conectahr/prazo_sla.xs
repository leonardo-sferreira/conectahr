// SLA vigente de um tipo de solicitacao (change sla-de-solicitacoes, D1 e D3): o setor responsavel, as horas
// uteis (72 sem linha ativa em `sla_config`) e as horas ate "perto de vencer" (80%, arredondado para baixo,
// no minimo 1). O endpoint soma as horas com `ConectaHR/somar_horas_uteis` (sem chamar funcao de funcao).
function "ConectaHR/prazo_sla" {
  input {
    text tipo_solicitacao filters=trim|lower
  }

  stack {
    var $setor {
      value = "rh"
    }

    conditional {
      if (($input.tipo_solicitacao == "ferias") || ($input.tipo_solicitacao == "correcao_ponto")) {
        var.update $setor {
          value = "gestor"
        }
      }

      elseif ($input.tipo_solicitacao == "acesso") {
        var.update $setor {
          value = "admin"
        }
      }
    }

    db.query sla_config {
      where = $db.sla_config.setor == $setor && $db.sla_config.tipo_solicitacao == $input.tipo_solicitacao && $db.sla_config.ativo == true
      return = {type: "single"}
    } as $config

    var $horas {
      value = ($config != null) ? $config.horas_uteis : 72
    }

    var $horas_alerta {
      value = (($horas * 8) / 10)|floor
    }

    conditional {
      if ($horas_alerta < 1) {
        var.update $horas_alerta {
          value = 1
        }
      }
    }
  }

  response = {setor: $setor, sla_horas: $horas, horas_alerta: $horas_alerta, configurado: ($config != null)}

  tags = ["conectahr"]
  guid = "conectahr-prazo-sla-0001"
}
