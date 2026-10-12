// Codigo hash (SHA-256) do registro tipo 7 do AFD (marcacao de ponto do REP-P,
// leiaute do MTE de 31/07/2026): SHA-256 da concatenacao dos campos 1 a 7 exatamente
// como saem no arquivo, seguida do hash do registro 7 anterior, quando existir.
//   1 NSR (9, zeros a esquerda) | 2 tipo "7" | 3 data e hora da marcacao (DH, 24)
//   4 CPF (12, zeros a esquerda) | 5 data e hora da gravacao (DH, 24)
//   6 coletor (2) | 7 "0" on-line ou "1" off-line
// Devolve {linha_base, hash}: a linha_base sao os campos 1 a 7, que o AFD reaproveita.
function "ConectaHR/hash_registro_rep" {
  input {
    int nsr
    text data_hora_marcacao_txt
    text cpf
    text data_hora_gravacao_txt
    text coletor
    bool offline
    text? hash_anterior
  }

  stack {
    var $nsr_texto {
      value = "000000000" ~ ($input.nsr|to_text)
    }

    var $nsr_campo {
      value = $nsr_texto|substr:(($nsr_texto|strlen) - 9):9
    }

    var $cpf_texto {
      value = "000000000000" ~ $input.cpf
    }

    var $cpf_campo {
      value = $cpf_texto|substr:(($cpf_texto|strlen) - 12):12
    }

    var $linha_base {
      value = $nsr_campo ~ "7" ~ $input.data_hora_marcacao_txt ~ $cpf_campo ~ $input.data_hora_gravacao_txt ~ $input.coletor ~ ($input.offline ? "1" : "0")
    }

    var $hash {
      value = ($linha_base ~ ($input.hash_anterior != null ? $input.hash_anterior : ""))|sha256
    }
  }

  response = {linha_base: $linha_base, hash: $hash}

  tags = ["conectahr"]
  guid = "conectahr-hash-registro-rep-0001"
}
