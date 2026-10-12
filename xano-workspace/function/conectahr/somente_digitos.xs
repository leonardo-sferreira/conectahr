// Devolve so os digitos de um texto ("12.345.678/0001-90" -> "12345678000190"), caractere
// por caractere (regex_replace nao esta disponivel de forma confiavel neste workspace).
function "ConectaHR/somente_digitos" {
  input {
    text? texto?
  }

  stack {
    var $caracteres {
      value = ($input.texto != null ? ($input.texto|split:"") : [])
    }

    var $digitos {
      value = ""
    }

    foreach ($caracteres) {
      each as $caractere {
        conditional {
          if ($caractere == "0" || $caractere == "1" || $caractere == "2" || $caractere == "3" || $caractere == "4" || $caractere == "5" || $caractere == "6" || $caractere == "7" || $caractere == "8" || $caractere == "9") {
            var.update $digitos {
              value = $digitos ~ $caractere
            }
          }
        }
      }
    }
  }

  response = $digitos

  tags = ["conectahr"]
  guid = "conectahr-somente-digitos-0001"
}
