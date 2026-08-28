// Valida um CPF localmente pelo algoritmo dos digitos verificadores.
// Normaliza removendo caracteres nao numericos, exige onze digitos,
// rejeita sequencias com o mesmo digito repetido e confere os dois
// digitos verificadores. Nao consulta nenhum servico externo.
function "ConectaHR/validar_cpf" {
  input {
    text cpf
  }

  stack {
    // Remove tudo que nao for digito, caractere por caractere
    // (regex_replace nao esta disponivel de forma confiavel neste workspace).
    var $caracteres_entrada {
      value = $input.cpf|split:""
    }

    var $cpf_normalizado {
      value = ""
    }

    foreach ($caracteres_entrada) {
      each as $caractere {
        var $eh_digito {
          value = ($caractere == "0" || $caractere == "1" || $caractere == "2" || $caractere == "3" || $caractere == "4" || $caractere == "5" || $caractere == "6" || $caractere == "7" || $caractere == "8" || $caractere == "9")
        }

        conditional {
          if ($eh_digito) {
            var.update $cpf_normalizado {
              value = $cpf_normalizado ~ $caractere
            }
          }
        }
      }
    }

    var $valido {
      value = true
    }

    var $motivo {
      value = ""
    }

    // Precisa ter exatamente onze digitos.
    conditional {
      if (($cpf_normalizado|strlen) != 11) {
        var.update $valido {
          value = false
        }

        var.update $motivo {
          value = "CPF deve conter onze digitos."
        }
      }
    }

    // Rejeita sequencias com o mesmo digito repetido.
    var $sequencia_repetida {
      value = ($cpf_normalizado == "00000000000" || $cpf_normalizado == "11111111111" || $cpf_normalizado == "22222222222" || $cpf_normalizado == "33333333333" || $cpf_normalizado == "44444444444" || $cpf_normalizado == "55555555555" || $cpf_normalizado == "66666666666" || $cpf_normalizado == "77777777777" || $cpf_normalizado == "88888888888" || $cpf_normalizado == "99999999999")
    }

    conditional {
      if ($valido && $sequencia_repetida) {
        var.update $valido {
          value = false
        }

        var.update $motivo {
          value = "CPF nao pode ser uma sequencia de digitos repetidos."
        }
      }
    }

    // Calcula o primeiro digito verificador (pesos de 10 a 2 sobre as nove primeiras posicoes).
    var $pesos_dv1 {
      value = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    }

    var $indice_dv1 {
      value = 0
    }

    var $soma_dv1 {
      value = 0
    }

    conditional {
      if ($valido) {
        foreach ($pesos_dv1) {
          each as $peso {
            var $digito_dv1 {
              value = ($cpf_normalizado|substr:$indice_dv1:1)|to_int
            }

            var.update $soma_dv1 {
              value = $soma_dv1 + ($digito_dv1 * $peso)
            }

            var.update $indice_dv1 {
              value = $indice_dv1 + 1
            }
          }
        }
      }
    }

    var $resto_dv1 {
      value = $soma_dv1|modulus:11
    }

    var $dv1_esperado {
      value = ($resto_dv1 < 2 ? 0 : 11 - $resto_dv1)
    }

    var $dv1_informado {
      value = ($cpf_normalizado|substr:9:1)|to_int
    }

    conditional {
      if ($valido && $dv1_esperado != $dv1_informado) {
        var.update $valido {
          value = false
        }

        var.update $motivo {
          value = "Primeiro digito verificador invalido."
        }
      }
    }

    // Calcula o segundo digito verificador (pesos de 11 a 2 sobre as dez primeiras posicoes).
    var $pesos_dv2 {
      value = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    }

    var $indice_dv2 {
      value = 0
    }

    var $soma_dv2 {
      value = 0
    }

    conditional {
      if ($valido) {
        foreach ($pesos_dv2) {
          each as $peso {
            var $digito_dv2 {
              value = ($cpf_normalizado|substr:$indice_dv2:1)|to_int
            }

            var.update $soma_dv2 {
              value = $soma_dv2 + ($digito_dv2 * $peso)
            }

            var.update $indice_dv2 {
              value = $indice_dv2 + 1
            }
          }
        }
      }
    }

    var $resto_dv2 {
      value = $soma_dv2|modulus:11
    }

    var $dv2_esperado {
      value = ($resto_dv2 < 2 ? 0 : 11 - $resto_dv2)
    }

    var $dv2_informado {
      value = ($cpf_normalizado|substr:10:1)|to_int
    }

    conditional {
      if ($valido && $dv2_esperado != $dv2_informado) {
        var.update $valido {
          value = false
        }

        var.update $motivo {
          value = "Segundo digito verificador invalido."
        }
      }
    }
  }

  response = {
    valido         : $valido
    motivo         : $motivo
    cpf_normalizado: $cpf_normalizado
  }

  tags = ["conectahr"]
  guid = "conectahr-validar-cpf-0001"
}
