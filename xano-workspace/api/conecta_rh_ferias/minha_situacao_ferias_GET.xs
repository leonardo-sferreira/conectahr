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

    // Saldo e periodos (change ponto-rep-p-e-ferias-clt, tarefa 6.2): a mesma conta de ferias/solicitacoes, na data
    // mais cedo em que a pessoa poderia comecar (hoje + antecedencia da matriz).
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador_autenticado.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra_aplicavel

    var $antecedencia_dias {
      value = ((($regra_aplicavel != null) && ($regra_aplicavel.antecedencia_ferias != null)) ? $regra_aplicavel.antecedencia_ferias : 0)
    }

    var $primeiro_inicio_possivel {
      value = now|add_secs_to_timestamp:($antecedencia_dias * 86400)|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    function.run "ConectaHR/situacao_ferias" {
      input = {colaborador_id: $colaborador_autenticado.id, data_referencia: $primeiro_inicio_possivel}
    } as $situacao

    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && $db.ferias.status == "Pendente"
      return = {type: "single"}
    } as $pendente_existente
  }

  response = {
    sucesso                  : true
    tipo_contrato            : $colaborador_autenticado.tipo_contrato
    data_admissao            : $colaborador_autenticado.data_admissao
    permite_solicitacao      : $situacao.permite_solicitacao
    primeiro_inicio_possivel : $primeiro_inicio_possivel
    antecedencia_minima_dias : $situacao.antecedencia_minima
    anos_completos           : $situacao.anos_completos
    proporcional             : $situacao.proporcional
    janela_inicio            : $situacao.janela_inicio
    janela_fim               : $situacao.janela_fim
    direito                  : $situacao.direito
    saldo                    : $situacao.saldo
    dias_usados              : $situacao.dias_usados
    dias_vendidos            : $situacao.dias_vendidos
    periodos                 : $situacao.periodos
    periodos_usados          : $situacao.periodos_usados
    maximo_periodos          : $situacao.maximo_periodos
    periodos_restantes       : $situacao.periodos_restantes
    permite_fracionamento    : $situacao.permite_fracionamento
    tem_periodo_14           : $situacao.tem_periodo_14
    minimo_principal         : $situacao.minimo_principal
    minimo_outros            : $situacao.minimo_outros
    minimo_dias_proximo      : $situacao.minimo_proximo
    maximo_abono             : $situacao.maximo_abono
    pode_vender              : $situacao.pode_vender
    limite_dias_por_pedido   : $situacao.saldo
    periodo_aquisitivo_meses : ($regra_aplicavel != null ? $regra_aplicavel.periodo_aquisitivo_meses : null)
    tem_pendente             : ($pendente_existente != null)
  }
  guid = "conectahr-minha-situacao-ferias-get-0001"
}
