// O Admin inclui uma conta ativa na comissao de etica (change canal-de-denuncias, D5); se ja foi membro,
// reativa. A pessoa recebe um aviso no sino. Auditado.
query "comissao_etica" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int user_id
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

    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente o Admin escolhe a comissao de etica."
    }

    db.get user {
      field_name = "id"
      field_value = $input.user_id
      output = ["id", "nome", "ativo"]
    } as $conta

    precondition (($conta != null) && ($conta.ativo == true)) {
      error_type = "notfound"
      error = "Conta nao encontrada ou inativa."
    }

    db.query comissao_etica {
      where = $db.comissao_etica.user_id == $conta.id
      return = {type: "single"}
    } as $existente

    precondition (($existente == null) || ($existente.ativo == false)) {
      error_type = "inputerror"
      error = "Esta pessoa ja e da comissao."
    }

    conditional {
      if ($existente == null) {
        db.add comissao_etica {
          data = {user_id: $conta.id, incluido_por_user_id: $usuario_autenticado.id, ativo: true, updated_at: "now"}
        } as $membro_criado
      }

      else {
        db.edit comissao_etica {
          field_name = "id"
          field_value = $existente.id
          data = {ativo: true, incluido_por_user_id: $usuario_autenticado.id, updated_at: "now"}
        } as $membro_reativado
      }
    }

    function.run "ConectaHR/notificar" {
      input = {destinatario_user_id: $conta.id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_novo", titulo: "Você entrou na comissão de ética", mensagem: "Agora você vê e apura as denúncias do canal, no item Denúncias do menu.", recurso: "denuncia"}
    } as $aviso_inclusao

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "incluir_comissao_etica"
        recurso    : "comissao_etica"
        registro_id: $conta.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Pessoa incluida na comissao."
  }

  guid = "conectahr-comissao-etica-post-0001"
}
