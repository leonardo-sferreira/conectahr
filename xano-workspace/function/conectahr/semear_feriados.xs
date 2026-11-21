// Carrega feriados e pontos facultativos que a BrasilAPI nao traz: os pontos facultativos federais da portaria do
// ano e os feriados do estado e da cidade de Sao Paulo (change ponto-rep-p-e-ferias-clt, tarefa 7.1). A lista vem de
// `tools/feriados.py --json`. Idempotente: pula a data que ja tem registro com a mesma abrangencia e o mesmo tipo
// (ex.: o Carnaval que a BrasilAPI ja gravou como ponto facultativo nacional). Rodada pela CLI (`xano function run`).
function "ConectaHR/semear_feriados" {
  input {
    json itens
  }

  stack {
    db.query feriado {
      return = {type: "list"}
      output = ["data", "abrangencia", "tipo"]
    } as $existentes

    var $chaves {
      value = ","
    }

    foreach ($existentes) {
      each as $e {
        var.update $chaves {
          value = $chaves ~ ($e.data|to_text) ~ "/" ~ $e.abrangencia ~ "/" ~ $e.tipo ~ ","
        }
      }
    }

    var $criados {
      value = 0
    }

    var $pulados {
      value = 0
    }

    foreach ($input.itens) {
      each as $item {
        var $chave {
          value = $item.data ~ "/" ~ $item.abrangencia ~ "/" ~ $item.tipo
        }

        conditional {
          if ($chaves|contains:("," ~ $chave ~ ",")) {
            var.update $pulados {
              value = $pulados + 1
            }
          }

          else {
            db.add feriado {
              data = {
                data       : $item.data
                nome       : $item.nome
                abrangencia: $item.abrangencia
                tipo       : $item.tipo
                observacao : $item.observacao
                estado     : $item.estado
                municipio  : $item.municipio
                ativo      : true
              }
            } as $novo

            var.update $chaves {
              value = $chaves ~ $chave ~ ","
            }

            var.update $criados {
              value = $criados + 1
            }
          }
        }
      }
    }
  }

  response = {criados: $criados, pulados: $pulados}

  tags = ["conectahr"]
  guid = "conectahr-semear-feriados-0001"
}
