// Altera o SLA de um tipo (change sla-de-solicitacoes, D4): as horas e, com ativo = false, a volta ao padrao de 72.
// So o Admin; de 1 a 720 horas uteis (240 no pedido LGPD). Auditado com o valor anterior e o novo. As
// solicitacoes ja abertas mantem o prazo gravado na abertura (D3).
query "sla_config/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int horas_uteis
    bool ativo
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
      error = "Somente o Admin altera o SLA de solicitacoes."
    }

    db.get sla_config {
      field_name = "id"
      field_value = $input.id
    } as $config

    precondition ($config != null) {
      error_type = "notfound"
      error = "SLA nao encontrado."
    }

    var $tipo_final {
      value = $config.tipo_solicitacao
    }

    precondition (($input.horas_uteis >= 1) && ($input.horas_uteis <= 720)) {
      error_type = "inputerror"
      error = "O SLA vai de 1 a 720 horas uteis."
    }

    precondition (($tipo_final != "privacidade_lgpd") || ($input.horas_uteis <= 240)) {
      error_type = "inputerror"
      error = "O pedido LGPD tem prazo legal de 15 dias: o SLA vai ate 240 horas uteis."
    }

    db.edit sla_config {
      field_name = "id"
      field_value = $config.id
      data = {
        horas_uteis           : $input.horas_uteis
        ativo                 : $input.ativo
        atualizado_por_user_id: $usuario_autenticado.id
        updated_at            : "now"
      }
    } as $config_editada

    var $valor_anterior {
      value = $tipo_final ~ ": " ~ ($config.ativo ? (($config.horas_uteis|to_text) ~ " horas uteis") : "72 horas uteis (padrao)")
    }

    var $valor_novo {
      value = $tipo_final ~ ": " ~ ($input.ativo ? (($input.horas_uteis|to_text) ~ " horas uteis") : "72 horas uteis (padrao)")
    }

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "alterar_sla"
        recurso       : "sla_config"
        registro_id   : $config.id
        resultado     : "sucesso"
        valor_anterior: $valor_anterior
        valor_novo    : $valor_novo
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "SLA alterado. Vale para as solicitacoes abertas daqui em diante."
    sla     : $config_editada
  }

  guid = "conectahr-sla-config-id-patch-0001"
}
