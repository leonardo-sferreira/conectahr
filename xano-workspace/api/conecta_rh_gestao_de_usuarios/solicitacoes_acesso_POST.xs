// Pedido do RH para o Admin trocar o perfil de acesso de uma conta (change pedido-de-acesso).
// So o RH pede (o Admin troca direto em usuarios/{id}/perfil). Um pedido pendente por conta;
// ninguem pede para a propria conta. Os Admins ativos recebem a notificacao.
query solicitacoes_acesso verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int usuario_id
    text perfil filters=trim
    text justificativa filters=trim
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

    precondition ($perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pede alteracao de acesso. O Admin altera direto."
    }

    db.get user {
      field_name = "id"
      field_value = $input.usuario_id
    } as $usuario_alvo

    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuario nao encontrado."
    }

    precondition ($usuario_alvo.id != $usuario_autenticado.id) {
      error_type = "inputerror"
      error = "Voce nao pode pedir alteracao do proprio acesso."
    }

    var $perfil_novo {
      value = $input.perfil|trim|to_upper
    }

    precondition (($perfil_novo == "ADMIN") || ($perfil_novo == "RH") || ($perfil_novo == "GESTOR") || ($perfil_novo == "COLABORADOR")) {
      error_type = "inputerror"
      error = "Perfil invalido. Use ADMIN, RH, GESTOR ou COLABORADOR."
    }

    var $perfil_valor_banco {
      value = ($perfil_novo == "ADMIN" ? "Admin" : ($perfil_novo == "RH" ? "RH" : ($perfil_novo == "GESTOR" ? "Gestor" : "Colaborador")))
    }

    precondition (($usuario_alvo.perfil|trim|to_upper) != $perfil_novo) {
      error_type = "inputerror"
      error = "A conta ja tem esse perfil."
    }

    precondition (($input.justificativa|strlen) >= 10) {
      error_type = "inputerror"
      error = "Explique o motivo do pedido em pelo menos 10 caracteres."
    }

    precondition (($input.justificativa|strlen) <= 1000) {
      error_type = "inputerror"
      error = "A justificativa pode ter no maximo 1000 caracteres."
    }

    db.query solicitacao_acesso {
      where = $db.solicitacao_acesso.usuario_id == $usuario_alvo.id && $db.solicitacao_acesso.status == "pendente"
      return = {type: "single"}
    } as $pedido_aberto

    precondition ($pedido_aberto == null) {
      error_type = "inputerror"
      error = "Ja existe um pedido de alteracao de acesso pendente para esta conta."
    }

    db.query colaborador {
      where = $db.colaborador.user_id == $usuario_alvo.id
      return = {type: "single"}
      output = ["id", "nome"]
    } as $colaborador_alvo

    db.add solicitacao_acesso {
      data = {
        usuario_id         : $usuario_alvo.id
        colaborador_id     : ($colaborador_alvo != null ? $colaborador_alvo.id : null)
        solicitante_user_id: $usuario_autenticado.id
        perfil_atual       : $usuario_alvo.perfil
        perfil_solicitado  : $perfil_valor_banco
        justificativa      : $input.justificativa
        status             : "pendente"
      }
    } as $pedido

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "solicitar_alteracao_perfil"
        recurso       : "solicitacao_acesso"
        registro_id   : $pedido.id
        valor_anterior: $usuario_alvo.perfil
        valor_novo    : $perfil_valor_banco
        resultado     : "sucesso"
      }
    } as $evento_auditoria

    db.query user {
      where = $db.user.perfil == "Admin" && $db.user.ativo == true
      return = {type: "list"}
      output = ["id"]
    } as $admins

    foreach ($admins) {
      each as $admin {
        function.run "ConectaHR/notificar" {
          input = {destinatario_user_id: $admin.id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_novo", titulo: "Pedido de alteracao de acesso", mensagem: $usuario_autenticado.nome ~ " pede o perfil " ~ $perfil_valor_banco ~ " para " ~ $usuario_alvo.nome ~ " (hoje " ~ $usuario_alvo.perfil ~ "). Aprove ou recuse em Usuarios e perfis.", recurso: "solicitacao_acesso", registro_id: $pedido.id}
        } as $aviso_admin
      }
    }
  }

  response = {
    sucesso    : true
    solicitacao: {id: $pedido.id, usuario_id: $pedido.usuario_id, perfil_atual: $pedido.perfil_atual, perfil_solicitado: $pedido.perfil_solicitado, status: $pedido.status}
  }

  guid = "conectahr-solicitacoes-acesso-post-0001"
}
