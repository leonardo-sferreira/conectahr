// RH/ADMIN publica um comunicado interno, com publico-alvo e vigencia.
query comunicados verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text titulo filters=trim|min:3|max:200
    text conteudo filters=trim|min:5|max:5000
    text publico_alvo filters=trim
    int? departamento_id?
    text? perfil_alvo? filters=trim
    date data_inicio
    date? data_fim?
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem publicar comunicados."
    }

    // Valida o publico-alvo usando os valores exatos do Enum.
    precondition ($input.publico_alvo == "todos" || $input.publico_alvo == "departamento" || $input.publico_alvo == "perfil") {
      error_type = "inputerror"
      error = "Publico-alvo invalido. Use todos, departamento ou perfil."
    }

    precondition ($input.publico_alvo != "departamento" || $input.departamento_id != null) {
      error_type = "inputerror"
      error = "Informe departamento_id quando o publico-alvo for departamento."
    }

    precondition ($input.publico_alvo != "perfil" || $input.perfil_alvo != null) {
      error_type = "inputerror"
      error = "Informe perfil_alvo quando o publico-alvo for perfil."
    }

    // Valida o departamento, quando informado.
    var $departamento_valido_id {
      value = null
    }

    conditional {
      if ($input.departamento_id != null) {
        db.get departamento {
          field_name = "id"
          field_value = $input.departamento_id
        } as $departamento_selecionado

        precondition ($departamento_selecionado != null) {
          error_type = "notfound"
          error = "Departamento nao encontrado."
        }

        var.update $departamento_valido_id {
          value = $departamento_selecionado.id
        }
      }
    }

    // Valida o perfil-alvo, quando informado.
    var $perfil_alvo_normalizado {
      value = null
    }

    conditional {
      if ($input.perfil_alvo != null) {
        var.update $perfil_alvo_normalizado {
          value = $input.perfil_alvo|trim|to_upper
        }

        precondition ($perfil_alvo_normalizado == "ADMIN" || $perfil_alvo_normalizado == "RH" || $perfil_alvo_normalizado == "COLABORADOR" || $perfil_alvo_normalizado == "GESTOR") {
          error_type = "inputerror"
          error = "Perfil-alvo invalido. Use Admin, RH, Colaborador ou Gestor."
        }
      }
    }

    precondition ($input.data_fim == null || $input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim nao pode ser anterior a data de inicio."
    }

    // O enum comunicado.perfil_alvo usa Title-case ("Admin"/"RH"/"Colaborador"/
    // "Gestor"), diferente do valor normalizado em maiusculas usado so para
    // validar acima — grava a forma exata do enum, nao a normalizada.
    var $perfil_alvo_para_salvar {
      value = ($perfil_alvo_normalizado == "ADMIN" ? "Admin" : ($perfil_alvo_normalizado == "RH" ? "RH" : ($perfil_alvo_normalizado == "COLABORADOR" ? "Colaborador" : ($perfil_alvo_normalizado == "GESTOR" ? "Gestor" : null))))
    }

    db.add comunicado {
      data = {
        titulo               : $input.titulo
        conteudo              : $input.conteudo
        publico_alvo           : $input.publico_alvo
        departamento_id         : $departamento_valido_id
        perfil_alvo              : $perfil_alvo_para_salvar
        data_inicio               : $input.data_inicio
        data_fim                   : $input.data_fim
        publicado_por_user_id       : $usuario_autenticado.id
        ativo                        : true
        updated_at                    : "now"
      }
    } as $comunicado_criado

    // Auditoria: publicacao de comunicado.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "publicar_comunicado"
        recurso    : "comunicado"
        registro_id: $comunicado_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    mensagem  : "Comunicado publicado com sucesso."
    comunicado: $comunicado_criado
  }

  guid = "conectahr-comunicados-post-0001"
}
