// SHA-256 de um texto, em hexadecimal minusculo (64 caracteres). Usado no codigo hash
// das marcacoes do REP-P (Portaria MTP 671/2021, AFD registro tipo 7, campo 8), que
// encadeia cada marcacao com a anterior. Conferido contra o vetor padrao:
// "abc" -> ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad.
function "ConectaHR/sha256_hex" {
  input {
    text texto
  }

  stack {
    var $hash {
      value = $input.texto|sha256
    }
  }

  response = $hash

  tags = ["conectahr"]
  guid = "conectahr-sha256-hex-0001"
}
