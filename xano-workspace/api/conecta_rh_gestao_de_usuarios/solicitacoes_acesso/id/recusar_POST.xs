// Recusa o pedido de acesso, com o motivo para o RH (change pedido-de-acesso). So o Admin decide; o pedido precisa estar pendente
// e nao pode ser da propria conta do Admin.
query "solicitacoes_acesso/{id}/recusar" verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    text motivo filters=trim
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente o Admin decide pedidos de alteracao de acesso."
    }

    db.get solicitacao_acesso {
      field_name = "id"
      field_value = $input.id
    } as $pedido

    precondition ($pedido != null) {
      error_type = "notfound"
      error = "Pedido de acesso nao encontrado."
    }

    precondition ($pedido.status == "pendente") {
      error_type = "inputerror"
      error = "Este pedido ja foi decidido."
    }

    precondition ($pedido.usuario_id != $usuario_autenticado.id) {
      error_type = "inputerror"
      error = "Voce nao pode decidir um pedido sobre o proprio acesso."
    }

    db.get user {
      field_name = "id"
      field_value = $pedido.usuario_id
    } as $usuario_alvo

    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "A conta do pedido nao existe mais."
    }

    precondition (($input.motivo|strlen) >= 5) {
      error_type = "inputerror"
      error = "Explique o motivo da recusa em pelo menos 5 caracteres."
    }

    precondition (($input.motivo|strlen) <= 1000) {
      error_type = "inputerror"
      error = "O motivo pode ter no maximo 1000 caracteres."
    }

    db.edit solicitacao_acesso {
      field_name = "id"
      field_value = $pedido.id
      data = {status: "recusada", decidido_por_user_id: $usuario_autenticado.id, data_decisao: "now", motivo_decisao: $input.motivo, updated_at: "now"}
    } as $pedido_decidido

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "recusar_alteracao_perfil"
        recurso      : "solicitacao_acesso"
        registro_id  : $pedido.id
        justificativa: $input.motivo
        resultado    : "sucesso"
      }
    } as $evento_auditoria

    function.run "ConectaHR/notificar" {
      input = {destinatario_user_id: $pedido.solicitante_user_id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_decidido", titulo: "Pedido de acesso recusado", mensagem: "O Admin recusou o perfil " ~ $pedido.perfil_solicitado ~ " para " ~ $usuario_alvo.nome ~ ". Motivo: " ~ $input.motivo, recurso: "solicitacao_acesso", registro_id: $pedido.id}
    } as $aviso_rh
  }

  response = {
    sucesso : true
    mensagem: "Pedido recusado."
  }

  guid = "conectahr-solicitacoes-acesso-recusar-0001"
}
