// Cancela uma solicitacao propria de ferias.
// Permite qualquer perfil com colaborador ativo vinculado.
// Somente solicitacoes pendentes podem ser canceladas.
query "ferias/{id}/cancelar" verb=POST {
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
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }
  
    // Contas inativas nao podem cancelar solicitacoes.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Localiza o colaborador pelo token.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Impede cancelamento por colaborador desligado.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode cancelar solicitacoes de ferias."
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
  
    // Somente o dono pode cancelar.
    precondition ($solicitacao.colaborador_id == $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para cancelar esta solicitacao de ferias."
    }
  
    // Normaliza o status atual.
    var $status_solicitacao {
      value = $solicitacao.status|trim|to_upper
    }
  
    // Somente solicitacoes pendentes podem ser canceladas.
    precondition ($status_solicitacao == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente solicitacoes pendentes podem ser canceladas."
    }
  
    // Cancela sem excluir o registro.
    db.edit ferias {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        status              : "Cancelada"
        decidido_por_user_id: $usuario_autenticado.id
        data_decisao        : "now"
        updated_at          : "now"
      }
    } as $solicitacao_cancelada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao de ferias cancelada com sucesso."
    solicitacao: $solicitacao_cancelada
  }

  guid = "lIVTw7kIYY0QyJozCCpF0D10ax4"
}