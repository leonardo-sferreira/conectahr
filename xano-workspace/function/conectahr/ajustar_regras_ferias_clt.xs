// Ajusta as ferias da regra CLT ativa (change ponto-rep-p-e-ferias-clt, D9 e tarefa 6.1): antecedencia de 45 dias,
// minimo de 5 dias nos outros periodos e venda (abono pecuniario) de ate 10 dias (CLT, arts. 134 e 143). Rodar a mao
// (xano function run); so muda esses tres campos e audita com os valores anteriores. Repetir nao muda nada.
function "ConectaHR/ajustar_regras_ferias_clt" {
  input {
  }

  stack {
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == "CLT" && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $clt

    precondition ($clt != null) {
      error_type = "notfound"
      error = "Nao ha regra CLT ativa."
    }

    var $mudou {
      value = (($clt.antecedencia_ferias != 45) || ($clt.minimo_outros_periodos != 5) || ($clt.maximo_abono != 10))
    }

    conditional {
      if ($mudou) {
        db.edit regra_contrato {
          field_name = "id"
          field_value = $clt.id
          data = {antecedencia_ferias: 45, minimo_outros_periodos: 5, maximo_abono: 10, updated_at: "now"}
        } as $clt_ajustada

        db.add auditoria {
          data = {
            acao          : "ajustar_regras_ferias_clt"
            recurso       : "regra_contrato"
            registro_id   : $clt.id
            valor_anterior: "antecedencia=" ~ ($clt.antecedencia_ferias|to_text) ~ "; minimo_outros=" ~ ($clt.minimo_outros_periodos|to_text) ~ "; maximo_abono=" ~ ($clt.maximo_abono|to_text)
            valor_novo    : "antecedencia=45; minimo_outros=5; maximo_abono=10"
            resultado     : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    regra_id: $clt.id
    alterada: $mudou
  }

  tags = ["conectahr"]
  guid = "conectahr-ajustar-regras-ferias-clt-0001"
}
