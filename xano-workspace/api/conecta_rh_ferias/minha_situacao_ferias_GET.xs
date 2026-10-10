// Situacao de ferias do usuario autenticado, so leitura (tarefa 23 da change
// concluir-frontend-streamlit). Devolve os mesmos numeros que ferias/solicitacoes
// (POST) confere antes de aceitar um pedido, calculados do mesmo jeito: limite de
// dias por pedido (proporcional ao tempo de casa, ate o limite da matriz), periodos
// ja usados (pendentes e aprovados) contra o maximo, minimo de dias do proximo
// periodo, antecedencia minima e se ja existe pedido pendente.
// Nao e um saldo de ferias: o backend ainda nao desconta os dias ja tirados (ver a
// tarefa 74). Nao recebe user_id nem colaborador_id.
query minha_situacao_ferias verb=GET {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }

    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode consultar ferias."
    }

    // Mesma regra da matriz que ferias/solicitacoes usa.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador_autenticado.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra_aplicavel

    var $permite_solicitacao {
      value = ($regra_aplicavel == null || $regra_aplicavel.permite_solicitacao_ferias != false)
    }

    // Limite de dias por pedido: proporcional ao tempo de casa, nunca acima do
    // limite integral da matriz (mesma conta de ferias/solicitacoes).
    var $tempo_casa_dias {
      value = null
    }

    conditional {
      if ($colaborador_autenticado.data_admissao != null) {
        var $data_admissao_ts_situacao {
          value = ($colaborador_autenticado.data_admissao|to_timestamp)
        }

        var $agora_situacao {
          value = now
        }

        var.update $tempo_casa_dias {
          value = ((($agora_situacao - $data_admissao_ts_situacao) / 86400000)|to_int)
        }
      }
    }

    var $limite_dias_proporcional {
      value = ($regra_aplicavel != null ? $regra_aplicavel.dias_ferias_recesso : null)
    }

    conditional {
      if ($regra_aplicavel != null && $regra_aplicavel.proporcional == true && $regra_aplicavel.periodo_aquisitivo_meses != null && $regra_aplicavel.dias_ferias_recesso != null && $tempo_casa_dias != null) {
        var.update $limite_dias_proporcional {
          value = ((($regra_aplicavel.dias_ferias_recesso * $tempo_casa_dias) / ($regra_aplicavel.periodo_aquisitivo_meses * 30))|to_int)
        }
      }
    }

    var $limite_dias_por_pedido {
      value = ($limite_dias_proporcional != null && $regra_aplicavel != null && $regra_aplicavel.dias_ferias_recesso != null && $limite_dias_proporcional > $regra_aplicavel.dias_ferias_recesso ? $regra_aplicavel.dias_ferias_recesso : $limite_dias_proporcional)
    }

    // Periodos ja usados (pendentes e aprovados), como ferias/solicitacoes conta.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && ($db.ferias.status == "Aprovada" || $db.ferias.status == "Pendente")
      return = {type: "list"}
    } as $ferias_existentes

    var $periodos_usados {
      value = ($ferias_existentes|count)
    }

    var $minimo_dias_proximo {
      value = ($periodos_usados == 0 ? ($regra_aplicavel != null ? $regra_aplicavel.minimo_periodo_principal : null) : ($regra_aplicavel != null ? $regra_aplicavel.minimo_outros_periodos : null))
    }

    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && $db.ferias.status == "Pendente"
      return = {type: "single"}
    } as $pendente_existente
  }

  response = {
    sucesso                 : true
    tipo_contrato           : $colaborador_autenticado.tipo_contrato
    data_admissao           : $colaborador_autenticado.data_admissao
    permite_solicitacao     : $permite_solicitacao
    limite_dias_por_pedido  : $limite_dias_por_pedido
    periodos_usados         : $periodos_usados
    maximo_periodos         : ($regra_aplicavel != null ? $regra_aplicavel.maximo_periodos : null)
    permite_fracionamento   : ($regra_aplicavel != null ? $regra_aplicavel.permite_fracionamento : null)
    minimo_dias_proximo     : $minimo_dias_proximo
    antecedencia_minima_dias: ($regra_aplicavel != null ? $regra_aplicavel.antecedencia_ferias : null)
    periodo_aquisitivo_meses: ($regra_aplicavel != null ? $regra_aplicavel.periodo_aquisitivo_meses : null)
    tem_pendente            : ($pendente_existente != null)
  }

  guid = "conectahr-minha-situacao-ferias-get-0001"
}
