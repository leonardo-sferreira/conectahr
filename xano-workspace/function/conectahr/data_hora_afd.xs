// Data e hora no formato DH do AFD e do AEJ (leiautes do MTE de 31/07/2026):
// "AAAA-MM-ddThh:mm:00ZZZZZ", com os segundos fixos em "00" e o fuso de Brasilia
// (ex.: "2021-04-27T16:44:00-0300"). Sem data, usa o momento atual.
function "ConectaHR/data_hora_afd" {
  input {
    timestamp? momento?
  }

  stack {
    var $base {
      value = ($input.momento != null ? $input.momento : now)
    }

    var $texto {
      value = ($base|format_timestamp:"Y-m-d":"America/Sao_Paulo") ~ "T" ~ ($base|format_timestamp:"H:i":"America/Sao_Paulo") ~ ":00" ~ ($base|format_timestamp:"O":"America/Sao_Paulo")
    }
  }

  response = $texto

  tags = ["conectahr"]
  guid = "conectahr-data-hora-afd-0001"
}
