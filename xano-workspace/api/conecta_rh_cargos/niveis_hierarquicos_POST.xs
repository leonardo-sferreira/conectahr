// RH e Admin cadastram um nivel hierarquico (change organograma-hierarquia, D3). Auditado.
query niveis_hierarquicos verb=POST {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
    text nome filters=trim|min:2|max:60
    int ordem filters=min:1|max:99
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem mudar a hierarquia."
    }

    db.query nivel_hierarquico {
      where = $db.nivel_hierarquico.nome == $input.nome
      return = {type: "single"}
    } as $mesmo_nome

    precondition ($mesmo_nome == null) {
      error_type = "inputerror"
      error = "Ja existe um nivel com esse nome."
    }

    db.add nivel_hierarquico {
      data = {
        nome      : $input.nome
        ordem     : $input.ordem
        ativo     : true
        updated_at: "now"
      }
    } as $nivel_criado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_nivel_hierarquico"
        recurso    : "nivel_hierarquico"
        registro_id: $nivel_criado.id
        valor_novo : "nome=" ~ $input.nome ~ "; ordem=" ~ ($input.ordem|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Nivel cadastrado."
    nivel   : $nivel_criado
  }

  guid = "conectahr-niveis-hierarquicos-post-0001"
}
