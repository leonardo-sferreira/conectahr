// Confirma o registro administrativo de uma ausencia aprovada.
// Operacao permitida somente para RH ou ADMIN.
// Somente uma ausencia Aprovada pode virar Registrado.
query "ausencias/{id}/registrar" verb=POST {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
    text observacao? filters=trim|max:1000
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }
  
    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem registrar a ausencia.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem registrar ausencias."
    }
  
    // Localiza a ausencia.
    db.get ausencia {
      field_name = "id"
      field_value = $input.id
    } as $ausencia_atual
  
    precondition ($ausencia_atual != null) {
      error_type = "notfound"
      error = "Ausencia nao encontrada."
    }
  
    // Somente ausencias Aprovadas podem ser registradas.
    var $status_atual {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_atual == "APROVADA") {
      error_type = "inputerror"
      error = "Somente ausencias com status Aprovada podem ser registradas."
    }
  
    // Confirma que o colaborador vinculado ainda existe.
    db.get colaborador {
      field_name = "id"
      field_value = $ausencia_atual.colaborador_id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador vinculado a ausencia nao encontrado."
    }
  
    // Preserva a observacao existente.
    var $observacao_final {
      value = $ausencia_atual.observacao
    }
  
    // Atualiza a observacao somente quando uma nova for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }
  
    // Confirma o registro da ausencia.
    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        status    : "Registrado"
        observacao: $observacao_final
        updated_at: "now"
      }
    } as $ausencia_registrada
  }

  response = {
    sucesso : true
    mensagem: "Ausencia registrada com sucesso."
    ausencia: $ausencia_registrada
  }

  guid = "nPRwy8_ltWRE-90Au1EpU4m5tr4"
}