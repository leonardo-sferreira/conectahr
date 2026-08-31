// Semeia a matriz inicial de jornada e ferias por tipo de contrato
// (CLT, PJ, ESTAGIO, APRENDIZ, TEMPORARIO, OUTRO), conforme definida em
// design.md - "Persistencia e integridade". Idempotente: so insere um
// tipo de contrato se ainda nao existir uma regra ativa para ele.
// Sem input - roda uma vez via `xano function run`, sem depender de
// autenticacao de usuario.
function "ConectaHR/semear_regras_contrato" {
  input {
  }

  stack {
    var $inseridos {
      value = []
    }

    // CLT: 8h/dia, 44h/semana, periodo aquisitivo de 12 meses, 30 dias,
    // proporcional, solicitacao habilitada, ate 3 periodos.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "CLT" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $clt_existente

    conditional {
      if ($clt_existente == null) {
        db.add regra_contrato {
          data = {
            tipo_contrato              : "CLT"
            horas_diarias              : 8
            horas_semanais             : 44
            intervalo_minutos          : 60
            permite_hora_extra         : true
            permite_banco_horas        : false
            controle_ponto             : "obrigatorio"
            periodo_aquisitivo_meses   : 12
            dias_ferias_recesso        : 30
            proporcional               : true
            permite_fracionamento      : true
            maximo_periodos            : 3
            minimo_periodo_principal   : 14
            antecedencia_ferias        : 30
            permite_solicitacao_ferias : true
            data_inicio                : "now"
            ativo                      : true
          }
        } as $clt_criado

        var.update $inseridos {
          value = $inseridos|push:"CLT"
        }
      }
    }

    // PJ: jornada e ferias nao aplicaveis no sistema.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "PJ" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $pj_existente

    conditional {
      if ($pj_existente == null) {
        db.add regra_contrato {
          data = {
            tipo_contrato              : "PJ"
            controle_ponto             : "nao_aplicavel"
            proporcional               : false
            permite_fracionamento      : false
            permite_solicitacao_ferias : false
            data_inicio                : "now"
            ativo                      : true
          }
        } as $pj_criado

        var.update $inseridos {
          value = $inseridos|push:"PJ"
        }
      }
    }

    // ESTAGIO: 6h/dia, 30h/semana, 12 meses, 30 dias de recesso,
    // proporcional, solicitacao habilitada, 1 periodo, sem hora extra.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "ESTAGIO" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $estagio_existente

    conditional {
      if ($estagio_existente == null) {
        db.add regra_contrato {
          data = {
            tipo_contrato              : "ESTAGIO"
            horas_diarias              : 6
            horas_semanais             : 30
            intervalo_minutos          : 15
            permite_hora_extra         : false
            permite_banco_horas        : false
            controle_ponto             : "obrigatorio"
            periodo_aquisitivo_meses   : 12
            dias_ferias_recesso        : 30
            proporcional               : true
            permite_fracionamento      : false
            maximo_periodos            : 1
            antecedencia_ferias        : 30
            permite_solicitacao_ferias : true
            data_inicio                : "now"
            ativo                      : true
          }
        } as $estagio_criado

        var.update $inseridos {
          value = $inseridos|push:"ESTAGIO"
        }
      }
    }

    // APRENDIZ: 6h/dia, 30h/semana, 12 meses, 30 dias, proporcional,
    // solicitacao habilitada, 1 periodo, sem hora extra nem banco de horas.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "APRENDIZ" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $aprendiz_existente

    conditional {
      if ($aprendiz_existente == null) {
        db.add regra_contrato {
          data = {
            tipo_contrato              : "APRENDIZ"
            horas_diarias              : 6
            horas_semanais             : 30
            intervalo_minutos          : 15
            permite_hora_extra         : false
            permite_banco_horas        : false
            controle_ponto             : "obrigatorio"
            periodo_aquisitivo_meses   : 12
            dias_ferias_recesso        : 30
            proporcional               : true
            permite_fracionamento      : false
            maximo_periodos            : 1
            antecedencia_ferias        : 30
            permite_solicitacao_ferias : true
            data_inicio                : "now"
            ativo                      : true
          }
        } as $aprendiz_criado

        var.update $inseridos {
          value = $inseridos|push:"APRENDIZ"
        }
      }
    }

    // TEMPORARIO: 8h/dia, 44h/semana, ferias proporcionais,
    // solicitacao desabilitada por padrao.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "TEMPORARIO" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $temporario_existente

    conditional {
      if ($temporario_existente == null) {
        db.add regra_contrato {
          data = {
            tipo_contrato              : "TEMPORARIO"
            horas_diarias              : 8
            horas_semanais             : 44
            intervalo_minutos          : 60
            permite_hora_extra         : true
            permite_banco_horas        : false
            controle_ponto             : "obrigatorio"
            proporcional               : true
            permite_fracionamento      : false
            permite_solicitacao_ferias : false
            data_inicio                : "now"
            ativo                      : true
          }
        } as $temporario_criado

        var.update $inseridos {
          value = $inseridos|push:"TEMPORARIO"
        }
      }
    }

    // OUTRO: todos os campos configuraveis manualmente pelo RH.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "OUTRO" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $outro_existente

    conditional {
      if ($outro_existente == null) {
        db.add regra_contrato {
          data = {
            tipo_contrato: "OUTRO"
            controle_ponto: "manual"
            data_inicio  : "now"
            ativo        : true
          }
        } as $outro_criado

        var.update $inseridos {
          value = $inseridos|push:"OUTRO"
        }
      }
    }

    // Confirma o estado final: uma regra ativa por tipo de contrato.
    db.query regra_contrato {
      where = $db.regra_contrato.ativo == true
      sort = {regra_contrato.tipo_contrato: "asc"}
      return = {type: "list"}
    } as $regras_ativas
  }

  response = {
    sucesso      : true
    inseridos    : $inseridos
    regras_ativas: $regras_ativas
  }

  tags = ["conectahr"]
  guid = "conectahr-semear-regras-contrato-0001"
}
