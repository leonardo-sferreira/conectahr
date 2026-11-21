// RH/ADMIN cadastra um feriado (nacional, estadual ou municipal) ou ponto facultativo (tipo, change ponto-rep-p-e-ferias-clt,
// tarefa 7.2). Auditado.
query feriados verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    date data
    text nome filters=trim|max:200
    text? abrangencia? filters=trim|lower
    // Feriado ou ponto facultativo (change ponto-rep-p-e-ferias-clt, tarefa 7.2).
    text? tipo? filters=trim|lower
    text? observacao? filters=trim|max:100
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

    precondition ((($input.nome|strlen) >= 3) && (($input.nome|strlen) <= 200)) {
      error_type = "inputerror"
      error = "O nome precisa ter de 3 a 200 caracteres."
    }

    var $abrangencia_final {
      value = (($input.abrangencia == null) || ($input.abrangencia == "")) ? "nacional" : $input.abrangencia
    }

    precondition (($abrangencia_final == "nacional") || ($abrangencia_final == "estadual") || ($abrangencia_final == "municipal")) {
      error_type = "inputerror"
      error = "Abrangencia invalida. Use nacional, estadual ou municipal."
    }

    var $tipo_final {
      value = (($input.tipo == null) || ($input.tipo == "")) ? "feriado" : $input.tipo
    }

    precondition (($tipo_final == "feriado") || ($tipo_final == "ponto_facultativo")) {
      error_type = "inputerror"
      error = "Tipo invalido. Use feriado ou ponto_facultativo."
    }

    precondition (($abrangencia_final == "nacional") || (($input.estado != null) && ($input.estado != ""))) {
      error_type = "inputerror"
      error = "Informe o estado do feriado estadual ou municipal."
    }

    precondition (($abrangencia_final != "municipal") || (($input.municipio != null) && ($input.municipio != ""))) {
      error_type = "inputerror"
      error = "Informe o municipio do feriado municipal."
    }

    var $estado_final {
      value = ($abrangencia_final == "nacional") ? null : $input.estado
    }

    var $municipio_final {
      value = ($abrangencia_final == "municipal") ? $input.municipio : null
    }

    db.add feriado {
      data = {
        data       : $input.data
        nome       : $input.nome
        abrangencia: $abrangencia_final
        tipo       : $tipo_final
        observacao : $input.observacao
        estado     : $estado_final
        municipio  : $municipio_final
        ativo      : true
      }
    } as $feriado_criado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_feriado"
        recurso    : "feriado"
        registro_id: $feriado_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Feriado cadastrado com sucesso."
    feriado : $feriado_criado
  }

  guid = "conectahr-feriados-post-0001"
}
