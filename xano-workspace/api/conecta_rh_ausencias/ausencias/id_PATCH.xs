// Atualiza uma solicitacao de ausencia do usuario autenticado.
// Somente o proprietario pode alterar enquanto estiver Pendente.
// Preserva o comprovante e a observacao quando nao forem enviados.
query "ausencias/{id}" verb=PATCH {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
    text tipo filters=trim
    date data_inicio
    date data_fim
    text motivo filters=trim|min:5|max:1000
    attachment? comprovante?
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
  
    // Localiza o colaborador vinculado ao usuario.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Confere o status profissional.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem atualizar ausencias."
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
  
    // Confere se a ausencia pertence ao usuario autenticado.
    precondition ($ausencia_atual.colaborador_id == $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para alterar esta ausencia."
    }
  
    // Somente registros Pendentes podem ser alterados.
    var $status_ausencia {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_ausencia == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente ausencias com status Pendente podem ser alteradas."
    }
  
    // Valida o periodo informado.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }
  
    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "Falta" || $input.tipo == "Atestado" || $input.tipo == "Afastamento" || $input.tipo == "Licenca" || $input.tipo == "Outro") {
      error_type = "inputerror"
      error = "Tipo de ausencia invalido."
    }
  
    // Mantem o comprovante atual quando nenhum arquivo novo for enviado.
    var $comprovante_final {
      value = $ausencia_atual.comprovante
    }
  
    // Mantem a observacao atual quando nenhuma nova for enviada.
    var $observacao_final {
      value = $ausencia_atual.observacao
    }
  
    // Processa um novo comprovante apenas quando ele for enviado.
    conditional {
      if ($input.comprovante != null) {
        storage.create_attachment {
          value = $input.comprovante
          access = "private"
          filename = ""
        } as $novo_comprovante
      
        var.update $comprovante_final {
          value = $novo_comprovante
        }
      }
    }
  
    // Atualiza a observacao apenas quando ela for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }
  
    // Atualiza somente os campos permitidos.
    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        tipo       : $input.tipo
        data_inicio: $input.data_inicio
        data_fim   : $input.data_fim
        motivo     : $input.motivo
        comprovante: $comprovante_final
        observacao : $observacao_final
        updated_at : "now"
      }
    } as $ausencia_atualizada
  }

  response = {
    sucesso : true
    mensagem: "Ausencia atualizada com sucesso."
    ausencia: $ausencia_atualizada
  }

  guid = "9kQ5xEyPrB2AFO7mOKPW0NS0N-s"
}