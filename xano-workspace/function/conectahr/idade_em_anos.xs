// Idade em anos completos aproximados a partir de uma data de nascimento
// (texto "Y-m-d"). Devolve null quando a data nao foi informada. Usa divisor
// inteiro 365 (mesma aproximacao de `documentos_pendentes_obrigatorios`); a
// imprecisao de ate 1 dia por ano nao muda a comparacao com 18 anos na pratica.
function "ConectaHR/idade_em_anos" {
  input {
    text? data_nascimento?
  }

  stack {
    var $idade {
      value = null
    }

    conditional {
      if ($input.data_nascimento != null && $input.data_nascimento != "") {
        var $nascimento_ts {
          value = $input.data_nascimento|to_timestamp
        }

        var $agora_idade {
          value = now
        }

        var.update $idade {
          value = (((($agora_idade - $nascimento_ts) / 86400000) / 365)|to_int)
        }
      }
    }
  }

  response = $idade

  tags = ["conectahr"]
  guid = "conectahr-idade-em-anos-0001"
}
