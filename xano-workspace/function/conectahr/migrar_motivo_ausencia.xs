// Migra os registros de ausencia que ainda nao tem `motivo_tipo` (lista fechada)
// para "outro". Roda uma vez via `xano function run`, sem input.
//
// O texto livre antigo (`ausencia.motivo`) NAO e apagado nem alterado: fica no
// banco, privado e fora de qualquer resposta de API, para nao perder historico
// (sem exclusao fisica). So `motivo_tipo` e preenchido.
//
// Idempotente: so toca registros com `motivo_tipo == null`; uma segunda execucao
// nao encontra nenhum e devolve contagem zero.
function "ConectaHR/migrar_motivo_ausencia" {
  input {
  }

  stack {
    db.query ausencia {
      where = $db.ausencia.motivo_tipo == null
      return = {type: "list"}
    } as $ausencias_sem_tipo

    var $total_migradas {
      value = 0
    }

    foreach ($ausencias_sem_tipo) {
      each as $ausencia_item {
        db.edit ausencia {
          field_name = "id"
          field_value = $ausencia_item.id
          data = {motivo_tipo: "outro"}
        } as $ausencia_migrada

        var.update $total_migradas {
          value = $total_migradas + 1
        }
      }
    }

    conditional {
      if ($total_migradas > 0) {
        db.add auditoria {
          data = {
            acao      : "migrar_motivo_ausencia"
            recurso   : "ausencia"
            valor_novo: ($total_migradas|to_text)
            resultado : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso         : true
    ausencias_migradas: $total_migradas
  }

  tags = ["conectahr"]
  guid = "conectahr-migrar-motivo-ausencia-0001"
}
