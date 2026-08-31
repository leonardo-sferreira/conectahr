// Rejeita uma solicitacao de ferias.
// Operacao permitida somente para RH ou ADMIN.
// Nao altera o colaborador ou seu acesso.
query "ferias/{id}/rejeitar" verb=POST {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_decisor
  
    precondition ($usuario_decisor != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }
  
    // Contas inativas nao podem rejeitar ferias.
    precondition ($usuario_decisor.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_decisor.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_decisor {
      value = $usuario_decisor.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem rejeitar.
    precondition ($perfil_decisor == "RH" || $perfil_decisor == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem rejeitar solicitacoes de ferias."
    }
  
    // Localiza a solicitacao.
    db.get ferias {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao
  
    precondition ($solicitacao != null) {
      error_type = "notfound"
      error = "Solicitacao de ferias nao encontrada."
    }
  
    // Normaliza o status atual.
    var $status_solicitacao {
      value = $solicitacao.status|trim|to_upper
    }
  
    // Somente solicitacoes pendentes podem ser rejeitadas.
    precondition ($status_solicitacao == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente solicitacoes pendentes podem ser rejeitadas."
    }
  
    // Confirma que o colaborador relacionado existe.
    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador relacionado a solicitacao nao encontrado."
    }
  
    // Registra a decisao.
    db.edit ferias {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        status              : "Rejeitada"
        decidido_por_user_id: $usuario_decisor.id
        data_decisao        : "now"
        updated_at          : "now"
      }
    } as $solicitacao_rejeitada

    // Auditoria: decisao de rejeicao de ferias.
    db.add auditoria {
      data = {
        user_id       : $usuario_decisor.id
        acao          : "rejeitar_ferias"
        recurso       : "ferias"
        registro_id   : $solicitacao.id
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao de ferias rejeitada com sucesso."
    solicitacao: $solicitacao_rejeitada
  }

  guid = "osHcoP-owTSHfHqzEmyenuhIFv0"
}