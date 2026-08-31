// Rejeita uma solicitacao de ausencia.
// Operacao permitida somente para RH ou ADMIN.
// A justificativa da rejeicao e obrigatoria.
query "ausencias/{id}/rejeitar" verb=POST {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
    text observacao filters=trim|min:5|max:1000
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
  
    // Somente RH ou ADMIN podem rejeitar.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem rejeitar ausencias."
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
  
    // Somente ausencias Pendentes podem ser rejeitadas.
    var $status_atual {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_atual == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente ausencias com status Pendente podem ser rejeitadas."
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
  
    // Rejeita a ausencia e registra a justificativa.
    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        status    : "Rejeitada"
        observacao: $input.observacao
        updated_at: "now"
      }
    } as $ausencia_rejeitada

    // Auditoria: decisao de rejeicao de ausencia.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "rejeitar_ausencia"
        recurso       : "ausencia"
        registro_id   : $ausencia_atual.id
        justificativa : $input.observacao
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Ausencia rejeitada com sucesso."
    ausencia: $ausencia_rejeitada
  }

  guid = "MHw4Su1K1n606zAdO_w2e4FUZuM"
}