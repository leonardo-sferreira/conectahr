// Cadastra um beneficio no catalogo (tarefa 82). Somente RH ou Admin. Recusa nome repetido.
query beneficios verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text nome filters=trim|min:2|max:100
    text tipo filters=trim
    text? operadora? filters=trim|max:100
    text? descricao? filters=trim|max:500
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    precondition (["vale_refeicao", "vale_alimentacao", "vale_transporte", "plano_saude", "plano_odontologico", "seguro_vida", "auxilio_home_office", "auxilio_creche", "outro"]|contains:$input.tipo) {
      error_type = "inputerror"
      error = "Tipo de beneficio invalido."
    }

    db.query beneficio {
      where = $db.beneficio.nome == $input.nome
      return = {type: "single"}
    } as $mesmo_nome

    precondition ($mesmo_nome == null) {
      error_type = "inputerror"
      error = "Ja existe um beneficio com este nome."
    }

    db.add beneficio {
      data = {
        nome              : $input.nome
        tipo              : $input.tipo
        operadora         : $input.operadora
        descricao         : $input.descricao
        ativo             : true
        criado_por_user_id: $usuario_autenticado.id
        updated_at        : "now"
      }
    } as $beneficio_criado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "cadastrar_beneficio"
        recurso    : "beneficio"
        registro_id: $beneficio_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    beneficio: $beneficio_criado
  }

  guid = "conectahr-beneficios-post-0001"
}
