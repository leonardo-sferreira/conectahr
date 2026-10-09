// Gera o hash (HMAC-SHA256) de um codigo de acesso de 6 digitos (OTP de login e
// codigo de redefinicao de senha), para que o codigo nunca fique em texto no banco.
// A chave junta o segredo $env.CODIGO_ACESSO_PEPPER (fora do banco; sem a variavel,
// vale so o id do usuario) com o id do usuario, e o mesmo codigo gera hashes
// diferentes para usuarios diferentes. Quem confere recalcula o hash do que foi
// digitado e compara com o gravado.
function "ConectaHR/hash_codigo_acesso" {
  input {
    int user_id
    text codigo
  }

  stack {
    var $chave {
      value = ($env.CODIGO_ACESSO_PEPPER != null ? $env.CODIGO_ACESSO_PEPPER : "") ~ ":" ~ ($input.user_id|to_text)
    }

    var $hash {
      value = $input.codigo|hmac_sha256:$chave
    }
  }

  response = $hash

  tags = ["conectahr"]
  guid = "conectahr-hash-codigo-acesso-0001"
}
