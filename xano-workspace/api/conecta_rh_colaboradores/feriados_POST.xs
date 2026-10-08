// RH/ADMIN cadastra um feriado (nacional, estadual ou municipal).
query feriados verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    date data
    text nome filters=trim|max:200
    text? abrangencia? filters=trim
    text? estado? filters=trim|max:100
    text? municipio? filters=trim|max:120
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem cadastrar feriados."
    }

    var $abrangencia_final {
      value = ($input.abrangencia != null ? $input.abrangencia : "nacional")
    }

    precondition ($abrangencia_final == "nacional" || $abrangencia_final == "estadual" || $abrangencia_final == "municipal") {
      error_type = "inputerror"
      error = "Abrangencia invalida. Use nacional, estadual ou municipal."
    }

    db.add feriado {
      data = {
        data          : $input.data
        nome             : $input.nome
        abrangencia         : $abrangencia_final
        estado                 : $input.estado
        municipio                 : $input.municipio
        ativo                        : true
      }
    } as $feriado_criado
  }

  response = {
    sucesso : true
    mensagem: "Feriado cadastrado com sucesso."
    feriado : $feriado_criado
  }

  guid = "conectahr-feriados-post-0001"
}
