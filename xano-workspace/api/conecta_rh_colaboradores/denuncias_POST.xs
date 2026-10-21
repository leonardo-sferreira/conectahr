// Registra uma denuncia no canal de etica (Lei 14.457/2022; change canal-de-denuncias, D3). Publico: funciona
// sem login, e nada liga a denuncia a uma conta (nem o token e lido). Devolve o protocolo e o codigo de
// acompanhamento (16 sinais), que so existe aqui: o banco guarda so o hash. Quem se identifica escreve nome e
// contato em `identificacao`. A comissao de etica recebe um aviso no sino, sem detalhe. Auditado sem usuario.
query "denuncias" verb=POST {
  api_group = "ConectaRH — Colaboradores"

  input {
    text tipo filters=trim|lower
    text relato filters=trim|max:4000
    text? quando? filters=trim|max:100
    text? envolvidos? filters=trim|max:200
    text? identificacao? filters=trim|max:200
  }

  stack {

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $tipo_agulha {
      value = "," ~ $input.tipo ~ ","
    }

    precondition (",assedio_moral,assedio_sexual,discriminacao,conduta_antietica,fraude,seguranca,outro,"|contains:$tipo_agulha) {
      error_type = "inputerror"
      error = "Escolha o tipo da denuncia."
    }

    precondition (($input.relato|strlen) >= 20) {
      error_type = "inputerror"
      error = "Conte o que aconteceu com pelo menos 20 caracteres."
    }

    var $identificacao {
      value = (($input.identificacao == null) ? "" : $input.identificacao)
    }

    var $alfabeto {
      value = "ABCDEFGHJKMNPQRSTVWXYZ23456789"
    }

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_0

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_1

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_2

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_3

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_4

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_5

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_6

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_7

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_8

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_9

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_10

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_11

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_12

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_13

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_14

    security.random_number {
      min = 0
      max = 29
    } as $sorteio_15

    var $codigo {
      value = ($alfabeto|substr:$sorteio_0:1) ~ ($alfabeto|substr:$sorteio_1:1) ~ ($alfabeto|substr:$sorteio_2:1) ~ ($alfabeto|substr:$sorteio_3:1) ~ ($alfabeto|substr:$sorteio_4:1) ~ ($alfabeto|substr:$sorteio_5:1) ~ ($alfabeto|substr:$sorteio_6:1) ~ ($alfabeto|substr:$sorteio_7:1) ~ ($alfabeto|substr:$sorteio_8:1) ~ ($alfabeto|substr:$sorteio_9:1) ~ ($alfabeto|substr:$sorteio_10:1) ~ ($alfabeto|substr:$sorteio_11:1) ~ ($alfabeto|substr:$sorteio_12:1) ~ ($alfabeto|substr:$sorteio_13:1) ~ ($alfabeto|substr:$sorteio_14:1) ~ ($alfabeto|substr:$sorteio_15:1)
    }

    var $chave_codigo {
      value = ($env.CODIGO_ACESSO_PEPPER != null ? $env.CODIGO_ACESSO_PEPPER : "") ~ ":denuncia"
    }

    var $codigo_hash {
      value = $codigo|hmac_sha256:$chave_codigo
    }

    db.add denuncia {
      data = {
        protocolo    : "DEN"
        codigo_hash  : $codigo_hash
        tipo         : $input.tipo
        relato       : $input.relato
        quando       : $input.quando
        envolvidos   : $input.envolvidos
        identificada : ($identificacao != "")
        identificacao: (($identificacao != "") ? $identificacao : null)
        recebida_em  : $hoje
        status       : "nova"
      }
    } as $denuncia_criada

    var $protocolo {
      value = "DEN-" ~ ($denuncia_criada.id|to_text)
    }

    db.edit denuncia {
      field_name = "id"
      field_value = $denuncia_criada.id
      data = {protocolo: $protocolo}
    } as $denuncia_com_protocolo

    var $denuncia_id_aviso {
      value = $denuncia_criada.id
    }

    db.query comissao_etica {
      where = $db.comissao_etica.ativo == true
      return = {type: "list"}
      output = ["user_id"]
    } as $membros_aviso

    foreach ($membros_aviso) {
      each as $membro_aviso {
        function.run "ConectaHR/notificar" {
          input = {destinatario_user_id: $membro_aviso.user_id, tipo: "pedido_novo", titulo: "Nova denúncia", mensagem: "A denúncia " ~ $protocolo ~ " chegou ao canal. Abra a fila Denúncias.", recurso: "denuncia", registro_id: $denuncia_id_aviso}
        } as $aviso_membro
      }
    }

    db.add auditoria {
      data = {
        acao       : "registrar_denuncia"
        recurso    : "denuncia"
        registro_id: $denuncia_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    var $codigo_exibicao {
      value = ($codigo|substr:0:4) ~ "-" ~ ($codigo|substr:4:4) ~ "-" ~ ($codigo|substr:8:4) ~ "-" ~ ($codigo|substr:12:4)
    }
  }

  response = {
    sucesso  : true
    protocolo: $protocolo
    codigo   : $codigo_exibicao
  }

  guid = "conectahr-denuncias-post-0001"
}
