// Grava o SLA de um tipo de solicitacao que ainda nao tem linha (change sla-de-solicitacoes, D4). O setor vem do
// tipo (D1). So o Admin; de 1 a 720 horas uteis (240 no pedido LGPD). Auditado com o valor anterior (o padrao, 72)
// e o novo. Mudar o SLA nao altera o prazo das solicitacoes ja abertas (D3).
query sla_config verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text tipo_solicitacao filters=trim|lower
    int horas_uteis
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

    var $tipo_final {
      value = $input.tipo_solicitacao
    }

    precondition ((",alteracao_cadastral,declaracao,documento_avulso,outra,privacidade_lgpd,desligamento,ferias,ausencia,correcao_ponto,acesso,")|contains:("," ~ $tipo_final ~ ",")) {
      error_type = "inputerror"
      error = "Tipo de solicitacao invalido."
    }

    var $setor_tipo {
      value = "rh"
    }

    conditional {
      if (($tipo_final == "ferias") || ($tipo_final == "correcao_ponto")) {
        var.update $setor_tipo {
          value = "gestor"
        }
      }

      elseif ($tipo_final == "acesso") {
        var.update $setor_tipo {
          value = "admin"
        }
      }
    }

    precondition (($input.horas_uteis >= 1) && ($input.horas_uteis <= 720)) {
      error_type = "inputerror"
      error = "O SLA vai de 1 a 720 horas uteis."
    }

    precondition (($tipo_final != "privacidade_lgpd") || ($input.horas_uteis <= 240)) {
      error_type = "inputerror"
      error = "O pedido LGPD tem prazo legal de 15 dias: o SLA vai ate 240 horas uteis."
    }

    db.query sla_config {
      where = $db.sla_config.setor == $setor_tipo && $db.sla_config.tipo_solicitacao == $tipo_final
      return = {type: "single"}
    } as $existente

    precondition ($existente == null) {
      error_type = "inputerror"
      error = "Este tipo ja tem SLA gravado: altere a linha existente."
    }

    db.add sla_config {
      data = {
        setor                 : $setor_tipo
        tipo_solicitacao      : $tipo_final
        horas_uteis           : $input.horas_uteis
        ativo                 : true
        atualizado_por_user_id: $usuario_autenticado.id
        updated_at            : "now"
      }
    } as $config_criada

    var $valor_novo {
      value = $tipo_final ~ ": " ~ ($input.horas_uteis|to_text) ~ " horas uteis"
    }

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "alterar_sla"
        recurso       : "sla_config"
        registro_id   : $config_criada.id
        resultado     : "sucesso"
        valor_anterior: $tipo_final ~ ": 72 horas uteis (padrao)"
        valor_novo    : $valor_novo
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "SLA gravado. Vale para as solicitacoes abertas daqui em diante."
    sla     : $config_criada
  }

  guid = "conectahr-sla-config-post-0001"
}
