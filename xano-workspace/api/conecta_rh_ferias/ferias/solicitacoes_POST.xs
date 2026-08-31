// Cria uma solicitacao de ferias para o usuario autenticado.
// Permite qualquer perfil com colaborador ativo vinculado.
// Nao recebe colaborador_id ou user_id.
query "ferias/solicitacoes" verb=POST {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    date data_inicio
    date data_fim
    int quantidade_dias filters=min:1|max:30
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
  
    // Contas inativas nao podem solicitar ferias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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
  
    // Somente colaborador profissionalmente ativo
    // pode criar uma solicitacao.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem solicitar ferias."
    }
  
    // A data final nao pode ser anterior a data inicial.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }

    // Regras contratuais de ferias (item 4.4): busca a linha da matriz
    // regra_contrato para o tipo_contrato do colaborador — essa e a
    // fonte normativa registrada na solicitacao.
    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador_autenticado.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra_aplicavel

    // PJ e TEMPORARIO tem solicitacao de ferias desabilitada por padrao
    // na matriz — bloqueia so quando a regra diz explicitamente false.
    precondition ($regra_aplicavel == null || $regra_aplicavel.permite_solicitacao_ferias != false) {
      error_type = "accessdenied"
      error = "Solicitacao de ferias nao habilitada para o tipo de contrato deste colaborador."
    }

    // Antecedencia minima exigida pela matriz. data_inicio e um campo
    // "date" (string) — precisa de |to_timestamp antes de aritmetica, e
    // o valor precisa estar pre-extraido antes de combinar com now (ver
    // conectahr-xano-platform-quirks, achado 13).
    var $data_inicio_ts {
      value = ($input.data_inicio|to_timestamp)
    }

    var $agora_antecedencia {
      value = now
    }

    var $antecedencia_dias_solicitacao {
      value = ((($data_inicio_ts - $agora_antecedencia) / 86400000)|to_int)
    }

    precondition ($regra_aplicavel == null || $regra_aplicavel.antecedencia_ferias == null || $antecedencia_dias_solicitacao >= $regra_aplicavel.antecedencia_ferias) {
      error_type = "inputerror"
      error = "A solicitacao nao atende a antecedencia minima exigida para o tipo de contrato."
    }

    // Proporcionalidade: limita a quantidade de dias ao acumulo
    // proporcional desde a admissao, nunca acima do limite integral
    // (dias_ferias_recesso) da matriz — cobre tambem o recesso de estagio.
    var $tempo_casa_dias {
      value = null
    }

    conditional {
      if ($colaborador_autenticado.data_admissao != null) {
        var $data_admissao_ts_ferias {
          value = ($colaborador_autenticado.data_admissao|to_timestamp)
        }

        var $agora_tempo_casa {
          value = now
        }

        var.update $tempo_casa_dias {
          value = ((($agora_tempo_casa - $data_admissao_ts_ferias) / 86400000)|to_int)
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

    var $limite_dias_final {
      value = ($limite_dias_proporcional != null && $regra_aplicavel != null && $regra_aplicavel.dias_ferias_recesso != null && $limite_dias_proporcional > $regra_aplicavel.dias_ferias_recesso ? $regra_aplicavel.dias_ferias_recesso : $limite_dias_proporcional)
    }

    precondition ($limite_dias_final == null || $input.quantidade_dias <= $limite_dias_final) {
      error_type = "inputerror"
      error = "A quantidade de dias solicitada excede o limite proporcional acumulado para este colaborador."
    }

    // Fracionamento: conta periodos ja pendentes/aprovados deste
    // colaborador contra o limite e o minimo de dias por periodo da matriz.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && ($db.ferias.status == "Aprovada" || $db.ferias.status == "Pendente")
      return = {type: "list"}
    } as $ferias_existentes

    var $quantidade_periodos_existentes {
      value = ($ferias_existentes|count)
    }

    precondition ($regra_aplicavel == null || $regra_aplicavel.maximo_periodos == null || $quantidade_periodos_existentes < $regra_aplicavel.maximo_periodos) {
      error_type = "inputerror"
      error = "O colaborador ja atingiu o numero maximo de periodos de ferias fracionados permitido."
    }

    precondition ($quantidade_periodos_existentes == 0 || ($regra_aplicavel != null && $regra_aplicavel.permite_fracionamento == true)) {
      error_type = "inputerror"
      error = "Fracionamento de ferias nao permitido para este tipo de contrato."
    }

    var $dias_minimos_exigidos {
      value = ($quantidade_periodos_existentes == 0 ? ($regra_aplicavel != null ? $regra_aplicavel.minimo_periodo_principal : null) : ($regra_aplicavel != null ? $regra_aplicavel.minimo_outros_periodos : null))
    }

    precondition ($dias_minimos_exigidos == null || $input.quantidade_dias >= $dias_minimos_exigidos) {
      error_type = "inputerror"
      error = "A quantidade de dias e menor que o minimo exigido para este periodo de ferias."
    }

    // Verifica se ja existe uma solicitacao pendente.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && $db.ferias.status == "Pendente"
      return = {type: "single"}
    } as $solicitacao_pendente
  
    precondition ($solicitacao_pendente == null) {
      error_type = "inputerror"
      error = "Ja existe uma solicitacao de ferias pendente para este colaborador."
    }
  
    // Cria a solicitacao com o status exato do Enum.
    var $regra_aplicavel_id {
      value = ($regra_aplicavel != null ? $regra_aplicavel.id : null)
    }

    db.add ferias {
      data = {
        colaborador_id  : $colaborador_autenticado.id
        data_solicitacao: "now"
        data_inicio     : $input.data_inicio
        data_fim        : $input.data_fim
        quantidade_dias : $input.quantidade_dias
        status          : "Pendente"
        regra_contrato_id: $regra_aplicavel_id
        updated_at      : "now"
      }
    } as $solicitacao_criada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao de ferias criada com sucesso e enviada para analise."
    solicitacao: $solicitacao_criada
  }

  guid = "ptQRsxyItifAF-IRd7jxeFPRPes"
}