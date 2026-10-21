// Quem denunciou responde a comissao pelo codigo (change canal-de-denuncias, D3). Publico. So enquanto a
// denuncia nao foi concluida. A comissao recebe um aviso no sino.
query "denuncias/responder" verb=POST {
  api_group = "ConectaRH — Colaboradores"

  input {
    text codigo filters=trim
    text texto filters=trim|max:2000
  }

  stack {

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

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

    precondition ($denuncia.status != "concluida") {
      error_type = "inputerror"
      error = "Esta denuncia ja foi concluida."
    }

    precondition (($input.texto|strlen) >= 2) {
      error_type = "inputerror"
      error = "Escreva a mensagem."
    }

    db.add denuncia_mensagem {
      data = {denuncia_id: $denuncia.id, autor: "denunciante", texto: $input.texto, enviada_em: $hoje}
    } as $mensagem_criada

    var $denuncia_id_aviso {
      value = $denuncia.id
    }

    db.query comissao_etica {
      where = $db.comissao_etica.ativo == true
      return = {type: "list"}
      output = ["user_id"]
    } as $membros_aviso

    foreach ($membros_aviso) {
      each as $membro_aviso {
        function.run "ConectaHR/notificar" {
          input = {destinatario_user_id: $membro_aviso.user_id, tipo: "pedido_novo", titulo: "Nova mensagem na denúncia", mensagem: "Quem enviou a denúncia " ~ $denuncia.protocolo ~ " respondeu.", recurso: "denuncia", registro_id: $denuncia_id_aviso}
        } as $aviso_membro
      }
    }

    db.add auditoria {
      data = {
        acao       : "mensagem_denunciante"
        recurso    : "denuncia"
        registro_id: $denuncia.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Mensagem enviada a comissao."
  }

  guid = "conectahr-denuncias-responder-post-0001"
}
