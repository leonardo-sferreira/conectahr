// A comissao de etica escreve para quem denunciou (change canal-de-denuncias, D4); a pessoa le pelo codigo.
// A primeira mensagem passa a denuncia de nova para em apuracao. So enquanto nao foi concluida. Auditado (quem
// da comissao escreveu fica so na auditoria, nao na mensagem). So membro ativo da comissao.
query "denuncias/{id}/mensagem" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text texto filters=trim|max:2000
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

    precondition ($denuncia.status != "concluida") {
      error_type = "inputerror"
      error = "Esta denuncia ja foi concluida."
    }

    precondition (($input.texto|strlen) >= 5) {
      error_type = "inputerror"
      error = "Escreva a mensagem (pelo menos 5 caracteres)."
    }

    db.add denuncia_mensagem {
      data = {denuncia_id: $denuncia.id, autor: "comissao", texto: $input.texto, enviada_em: $hoje}
    } as $mensagem_criada

    conditional {
      if ($denuncia.status == "nova") {
        db.edit denuncia {
          field_name = "id"
          field_value = $denuncia.id
          data = {status: "em_apuracao"}
        } as $denuncia_em_apuracao
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "mensagem_comissao_denuncia"
        recurso    : "denuncia"
        registro_id: $denuncia.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Mensagem enviada."
  }

  guid = "conectahr-denuncias-mensagem-post-0001"
}
