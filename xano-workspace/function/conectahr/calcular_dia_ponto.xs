// Calculo do dia de ponto a partir das marcacoes da ARP e dos tratamentos (change
// ponto-rep-p-e-ferias-clt, design D4), sem acesso ao banco.
//   marcacoes: [{id, ms}] (ms = data e hora em milissegundos)
//   desconsideradas: [id] das marcacoes desconsideradas por tratamento
//   inclusoes: [ms] das marcacoes incluidas por tratamento
// Junta as validas (originais menos as desconsideradas, mais as incluidas), ordena,
// forma os pares entrada e saida em ordem e soma as horas dos pares completos.
// Status: "Ajustado" se houve tratamento; "Completo" com numero par de marcacoes;
// "Aberto" com numero impar no dia de hoje; "Incompleto" com impar em dia anterior.
function "ConectaHR/calcular_dia_ponto" {
  input {
    json marcacoes
    json? desconsideradas?
    json? inclusoes?
    bool e_hoje?=false
    decimal? horas_diarias?
  }

  stack {
    var $descartar {
      value = ($input.desconsideradas != null ? $input.desconsideradas : [])
    }

    // Lista de ids como texto (",9,12,"): o contains em lista de numeros vinda de json
    // nao reconhece o id.
    var $descartar_txt {
      value = "," ~ ($descartar|join:",") ~ ","
    }

    var $validas {
      value = []
    }

    foreach ($input.marcacoes) {
      each as $m {
        conditional {
          if (($descartar_txt|contains:("," ~ ($m.id|to_text) ~ ",")) == false) {
            var.update $validas {
              value = $validas|push:{ms: $m.ms, incluida: false}
            }
          }
        }
      }
    }

    foreach (($input.inclusoes != null ? $input.inclusoes : [])) {
      each as $ms_incluida {
        var.update $validas {
          value = $validas|push:{ms: $ms_incluida, incluida: true}
        }
      }
    }

    var $ordenadas {
      value = $validas|sort:"ms":"number":true
    }

    var $total {
      value = $ordenadas|count
    }

    var $trabalhado_ms {
      value = 0
    }

    var $entrada_ms {
      value = 0
    }

    var $aberta {
      value = false
    }

    foreach ($ordenadas) {
      each as $item {
        conditional {
          if ($aberta) {
            var.update $trabalhado_ms {
              value = $trabalhado_ms + ($item.ms - $entrada_ms)
            }

            var.update $aberta {
              value = false
            }
          }

          else {
            var.update $entrada_ms {
              value = $item.ms
            }

            var.update $aberta {
              value = true
            }
          }
        }
      }
    }

    var $horas {
      value = $trabalhado_ms / 3600000
    }

    var $houve_tratamento {
      value = (($descartar|count) > 0) || (($input.inclusoes != null ? ($input.inclusoes|count) : 0) > 0)
    }

    var $status {
      value = ($houve_tratamento ? "Ajustado" : ($aberta == false ? "Completo" : ($input.e_hoje ? "Aberto" : "Incompleto")))
    }

    var $extras {
      value = (($input.horas_diarias != null && $horas > $input.horas_diarias) ? ($horas - $input.horas_diarias) : 0)
    }
  }

  response = {marcacoes: $ordenadas, quantidade: $total, horas_trabalhadas: $horas, horas_extras: $extras, status: $status}

  tags = ["conectahr"]
  guid = "conectahr-calcular-dia-ponto-0001"
}
