// Membros ativos da comissao de etica, com nome e perfil (change canal-de-denuncias, D5). So o Admin.
query "comissao_etica" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    db.query comissao_etica {
      where = $db.comissao_etica.ativo == true
      return = {type: "list"}
    } as $membros_ativos

    var $membros {
      value = []
    }

    foreach ($membros_ativos) {
      each as $m {
        db.get user {
          field_name = "id"
          field_value = $m.user_id
          output = ["id", "nome", "perfil"]
        } as $conta_membro

        var.update $membros {
          value = $membros|push:{id: $m.id, user_id: $m.user_id, nome: ($conta_membro != null ? $conta_membro.nome : null), perfil: ($conta_membro != null ? $conta_membro.perfil : null)}
        }
      }
    }
  }

  response = {
    sucesso: true
    membros: $membros
  }

  guid = "conectahr-comissao-etica-get-0001"
}
