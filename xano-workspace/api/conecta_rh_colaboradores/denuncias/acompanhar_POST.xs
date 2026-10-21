// Acompanha uma denuncia pelo codigo (change canal-de-denuncias, D3). Publico, como o envio: devolve o
// protocolo, o tipo, a situacao, o resultado e o parecer, quando concluida, e a conversa com a comissao (lado
// e data, sem quem da comissao escreveu). Nao devolve a identificacao. POST para o codigo nao ir na URL.
query "denuncias/acompanhar" verb=POST {
  api_group = "ConectaRH — Colaboradores"

  input {
    text codigo filters=trim
  }

  stack {

    var $codigo_normalizado {
      value = $input.codigo|to_upper|replace:"-":""|replace:" ":""
    }

    precondition (($codigo_normalizado|strlen) == 16) {
      error_type = "inputerror"
      error = "O codigo tem 16 letras e numeros (pode digitar com ou sem os hifens)."
    }

    var $chave_codigo {
      value = ($env.CODIGO_ACESSO_PEPPER != null ? $env.CODIGO_ACESSO_PEPPER : "") ~ ":denuncia"
    }

    var $codigo_hash {
      value = $codigo_normalizado|hmac_sha256:$chave_codigo
    }

    db.query denuncia {
      where = $db.denuncia.codigo_hash == $codigo_hash
      return = {type: "single"}
    } as $denuncia

    precondition ($denuncia != null) {
      error_type = "notfound"
      error = "Codigo nao encontrado. Confira as letras e os numeros."
    }

    db.query denuncia_mensagem {
      where = $db.denuncia_mensagem.denuncia_id == $denuncia.id
      sort = {denuncia_mensagem.id: "asc"}
      return = {type: "list"}
      output = ["autor", "texto", "enviada_em"]
    } as $mensagens
  }

  response = {
    sucesso    : true
    protocolo  : $denuncia.protocolo
    tipo       : $denuncia.tipo
    status     : $denuncia.status
    recebida_em: $denuncia.recebida_em
    resultado  : $denuncia.resultado
    parecer    : $denuncia.parecer
    mensagens  : $mensagens
  }

  guid = "conectahr-denuncias-acompanhar-post-0001"
}
