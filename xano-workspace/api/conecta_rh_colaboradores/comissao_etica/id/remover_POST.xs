// O Admin tira uma pessoa da comissao de etica (change canal-de-denuncias, D5): so desativa. Auditado.
query "comissao_etica/{id}/remover" verb=POST {
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

    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente o Admin escolhe a comissao de etica."
    }

    db.get comissao_etica {
      field_name = "id"
      field_value = $input.id
    } as $membro

    precondition (($membro != null) && ($membro.ativo == true)) {
      error_type = "notfound"
      error = "Membro nao encontrado."
    }

    db.edit comissao_etica {
      field_name = "id"
      field_value = $membro.id
      data = {ativo: false, updated_at: "now"}
    } as $membro_removido

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "remover_comissao_etica"
        recurso    : "comissao_etica"
        registro_id: $membro.user_id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Pessoa removida da comissao."
  }

  guid = "conectahr-comissao-etica-remover-post-0001"
}
