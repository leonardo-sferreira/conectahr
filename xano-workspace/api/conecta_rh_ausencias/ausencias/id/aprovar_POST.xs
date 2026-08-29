// Aprova uma solicitacao de ausencia.
// Operacao permitida somente para RH ou ADMIN.
// Nao altera o colaborador nem exclui o registro.
query "ausencias/{id}/aprovar" verb=POST {
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
  
    // Somente RH ou ADMIN podem aprovar.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem aprovar ausencias."
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
  
    // Somente ausencias Pendentes podem ser aprovadas.
    var $status_atual {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_atual == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente ausencias com status Pendente podem ser aprovadas."
    }
  
    // Confirma que o colaborador ainda existe.
    db.get colaborador {
      field_name = "id"
      field_value = $ausencia_atual.colaborador_id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador vinculado a ausencia nao encontrado."
    }
  
    // Preserva a observacao existente por padrao.
    var $observacao_final {
      value = $ausencia_atual.observacao
    }
  
    // Substitui a observacao somente quando uma nova for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }
  
    // Aprova a ausencia.
    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        status    : "Aprovada"
        observacao: $observacao_final
        updated_at: "now"
      }
    } as $ausencia_aprovada
  }

  response = {
    sucesso : true
    mensagem: "Ausencia aprovada com sucesso."
    ausencia: $ausencia_aprovada
  }

  guid = "4O4xdTdSyFE1ljfTuGbsFaasY2g"
}