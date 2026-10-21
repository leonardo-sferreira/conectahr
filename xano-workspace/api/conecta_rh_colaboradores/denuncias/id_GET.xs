// Detalhe de uma denuncia para a comissao de etica (change canal-de-denuncias, D4): o relato, quando,
// envolvidos, a identificacao (se a pessoa se identificou), a situacao, o resultado, o parecer e a conversa.
// Cada abertura fica na auditoria (abrir_denuncia). So membro ativo da comissao.
query "denuncias/{id}" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    db.query comissao_etica {
      where = $db.comissao_etica.user_id == $usuario_autenticado.id && $db.comissao_etica.ativo == true
      return = {type: "single"}
    } as $membro_comissao

    precondition ($membro_comissao != null) {
      error_type = "accessdenied"
      error = "So a comissao de etica ve as denuncias."
    }

    db.get denuncia {
      field_name = "id"
      field_value = $input.id
    } as $denuncia

    precondition ($denuncia != null) {
      error_type = "notfound"
      error = "Denuncia nao encontrada."
    }

    db.query denuncia_mensagem {
      where = $db.denuncia_mensagem.denuncia_id == $denuncia.id
      sort = {denuncia_mensagem.id: "asc"}
      return = {type: "list"}
      output = ["autor", "texto", "enviada_em"]
    } as $mensagens

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "abrir_denuncia"
        recurso    : "denuncia"
        registro_id: $denuncia.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    denuncia : {id: $denuncia.id, protocolo: $denuncia.protocolo, tipo: $denuncia.tipo, relato: $denuncia.relato, quando: $denuncia.quando, envolvidos: $denuncia.envolvidos, identificada: $denuncia.identificada, identificacao: $denuncia.identificacao, recebida_em: $denuncia.recebida_em, status: $denuncia.status, resultado: $denuncia.resultado, parecer: $denuncia.parecer, concluida_em: $denuncia.concluida_em}
    mensagens: $mensagens
  }

  guid = "conectahr-denuncias-id-get-0001"
}
