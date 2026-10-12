// Importa os feriados nacionais de um ano da BrasilAPI (https://brasilapi.com.br/api/feriados/v1/{ano}),
// API publica e gratuita: so o ano vai na requisicao, nenhum dado pessoal (change
// ponto-rep-p-e-ferias-clt, tarefa 7.1, decisao do usuario em 12/10/2026). Grava so as datas
// que ainda nao tem feriado nacional cadastrado; nao mexe nos que ja existem nem nos estaduais
// e municipais. Carnaval e Corpus Christi entram como ponto facultativo: sao facultativos no
// servico publico federal, nao feriados em lei.
function "ConectaHR/importar_feriados_nacionais" {
  input {
    int ano
  }

  stack {
    precondition ($input.ano >= 2000 && $input.ano <= 2100) {
      error_type = "inputerror"
      error = "Informe um ano entre 2000 e 2100."
    }

    api.request {
      url = "https://brasilapi.com.br/api/feriados/v1/" ~ ($input.ano|to_text)
      method = "GET"
    } as $resposta_brasilapi

    precondition ($resposta_brasilapi.response.status == 200) {
      error_type = "standard"
      error = "Nao foi possivel buscar os feriados na BrasilAPI agora. Tente de novo em instantes."
    }

    var $inicio_ano {
      value = ($input.ano|to_text) ~ "-01-01"
    }

    var $fim_ano {
      value = ($input.ano|to_text) ~ "-12-31"
    }

    db.query feriado {
      where = $db.feriado.data >= $inicio_ano && $db.feriado.data <= $fim_ano
      return = {type: "list"}
    } as $feriados_do_ano

    // Datas que ja tem feriado nacional, como texto (",2026-01-01,"): o contains em lista nao
    // reconhece o item.
    var $datas_nacionais {
      value = ","
    }

    foreach ($feriados_do_ano) {
      each as $existente {
        conditional {
          if ($existente.abrangencia == "nacional") {
            var.update $datas_nacionais {
              value = $datas_nacionais ~ ($existente.data|format_timestamp:"Y-m-d":"UTC") ~ ","
            }
          }
        }
      }
    }

    var $importados {
      value = []
    }

    var $ja_existiam {
      value = 0
    }

    foreach ($resposta_brasilapi.response.result) {
      each as $item {
        conditional {
          if ($datas_nacionais|contains:("," ~ $item.date ~ ",")) {
            var.update $ja_existiam {
              value = $ja_existiam + 1
            }
          }

          else {
            db.add feriado {
              data = {
                data       : $item.date
                nome       : $item.name
                abrangencia: "nacional"
                tipo       : ($item.name == "Carnaval" || $item.name == "Corpus Christi" ? "ponto_facultativo" : "feriado")
                ativo      : true
              }
            } as $feriado_novo

            var.update $importados {
              value = $importados|push:$item.date
            }

            var.update $datas_nacionais {
              value = $datas_nacionais ~ $item.date ~ ","
            }
          }
        }
      }
    }
  }

  response = {
    ano        : $input.ano
    importados : $importados
    ja_existiam: $ja_existiam
  }

  tags = ["conectahr"]
  guid = "conectahr-importar-feriados-nacionais-0001"
}
