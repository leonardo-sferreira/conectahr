// Consolida as respostas legadas de `resposta_clima` (gravadas uma a uma,
// antes da change corrigir-brechas-e-alinhar-documentacao) nos contadores
// anonimos de `resposta_clima_agregado`. Roda uma vez via
// `xano function run`, sem input.
//
// Idempotente: grava um evento `consolidar_resposta_clima_legado` em
// `auditoria` ao final e, se esse evento ja existir, nao faz nada. Nao
// apaga nem altera as linhas legadas (sem exclusao fisica); elas deixam
// de ser lidas por qualquer endpoint.
function "ConectaHR/consolidar_resposta_clima_legado" {
  input {
  }

  stack {
    db.query auditoria {
      where = $db.auditoria.acao == "consolidar_resposta_clima_legado"
      return = {type: "single"}
    } as $execucao_anterior

    var $linhas_legadas {
      value = 0
    }

    var $departamento_agregado {
      value = 0
    }

    conditional {
      if ($execucao_anterior == null) {
        db.query resposta_clima {
          return = {type: "list"}
        } as $respostas_legadas

        foreach ($respostas_legadas) {
          each as $resposta_item {
            var.update $departamento_agregado {
              value = ($resposta_item.departamento_id == null ? 0 : $resposta_item.departamento_id)
            }

            db.query resposta_clima_agregado {
              where = $db.resposta_clima_agregado.pergunta_clima_id == $resposta_item.pergunta_clima_id && $db.resposta_clima_agregado.departamento_id == $departamento_agregado && $db.resposta_clima_agregado.nota == $resposta_item.nota
              return = {type: "single"}
            } as $contador_existente

            conditional {
              if ($contador_existente == null) {
                db.add resposta_clima_agregado {
                  data = {
                    pergunta_clima_id: $resposta_item.pergunta_clima_id
                    departamento_id  : $departamento_agregado
                    nota             : $resposta_item.nota
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

            var.update $linhas_legadas {
              value = $linhas_legadas + 1
            }
          }
        }

        db.add auditoria {
          data = {
            acao      : "consolidar_resposta_clima_legado"
            recurso   : "resposta_clima_agregado"
            valor_novo: ($linhas_legadas|to_text)
            resultado : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso             : true
    ja_executada_antes  : ($execucao_anterior != null)
    linhas_consolidadas : $linhas_legadas
  }

  tags = ["conectahr"]
  guid = "conectahr-consolidar-resposta-clima-legado-0001"
}
