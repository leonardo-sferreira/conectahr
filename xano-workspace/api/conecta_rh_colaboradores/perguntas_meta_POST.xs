// Cria uma pergunta do formulario de metas (change ciclo-de-metas, D2). So RH e Admin; auditado.
query "perguntas_meta" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text texto filters=trim|min:5|max:300
    text? orientacao? filters=trim|max:1000
    int ordem
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

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.add pergunta_meta {
      data = {texto: $input.texto, orientacao: $input.orientacao, ordem: $input.ordem, ativa: true, updated_at: "now"}
    } as $pergunta_criada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_pergunta_meta"
        recurso    : "pergunta_meta"
        registro_id: $pergunta_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Pergunta criada."
    pergunta: $pergunta_criada
  }

  guid = "conectahr-perguntas-meta-post-0001"
}
