// A URL assinada da foto da propria pessoa, para o menu da conta (change foto-de-perfil, D5). Vale 10 minutos;
// a tela guarda por menos que isso. Sem foto (ou sem ficha), foto_url nula: a tela mostra as iniciais.
query "minha_foto" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $foto_url {
      value = null
    }

    conditional {
      if (($colaborador_autenticado != null) && ($colaborador_autenticado.foto_path != null)) {
        var $lista_caminho {
          value = [$colaborador_autenticado.foto_path]
        }

        function.run "ConectaHR/assinar_fotos" {
          input = {caminhos: $lista_caminho}
        } as $assinadas

        var.update $foto_url {
          value = $assinadas|get:$colaborador_autenticado.foto_path
        }
      }
    }
  }

  response = {
    sucesso : true
    foto_url: $foto_url
  }

  guid = "conectahr-minha-foto-get-0001"
}
