// Verifica conflitos de uma solicitacao de ferias antes da decisao:
// sobreposicao com outras ferias/ausencias aprovadas do mesmo
// colaborador, antecedencia da solicitacao, periodo aquisitivo (contra
// a regra do tipo de contrato) e quantos colegas do mesmo departamento
// ja estao de ferias aprovadas no mesmo periodo (disponibilidade da
// equipe). So informa - nao bloqueia a decisao, que continua manual
// (RH/Gestor decidem conforme a politica).
query "ferias/{id}/verificar_conflito" verb=GET {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    int id
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente RH, ADMIN ou Gestor podem verificar conflitos de ferias."
    }

    db.get ferias {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao

    precondition ($solicitacao != null) {
      error_type = "notfound"
      error = "Solicitacao de ferias nao encontrada."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador_solicitante

    precondition ($colaborador_solicitante != null) {
      error_type = "notfound"
      error = "Colaborador relacionado a solicitacao nao encontrado."
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    // Antecedencia da solicitacao, em dias. data_inicio e data_admissao
    // sao campos "date" (string) — precisam de |to_timestamp antes de
    // aritmetica, com o valor pre-extraido antes de combinar com now
    // (ver conectahr-xano-platform-quirks, achado 13).
    var $data_inicio_conflito_ts {
      value = ($solicitacao.data_inicio|to_timestamp)
    }

    var $agora_conflito {
      value = now
    }

    var $antecedencia_dias {
      value = ((($data_inicio_conflito_ts - $agora_conflito) / 86400000)|to_int)
    }

    // Tempo de casa em dias, para comparar com o periodo aquisitivo.
    var $tempo_casa_dias {
      value = null
    }

    conditional {
      if ($colaborador_solicitante.data_admissao != null) {
        var $data_admissao_conflito_ts {
          value = ($colaborador_solicitante.data_admissao|to_timestamp)
        }

        var.update $tempo_casa_dias {
          value = ((($agora_conflito - $data_admissao_conflito_ts) / 86400000)|to_int)
        }
      }
    }

    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador_solicitante.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra_do_contrato

    var $periodo_aquisitivo_cumprido {
      value = true
    }

    conditional {
      if ($regra_do_contrato != null && $regra_do_contrato.periodo_aquisitivo_meses != null && $tempo_casa_dias != null) {
        var.update $periodo_aquisitivo_cumprido {
          value = ($tempo_casa_dias >= ($regra_do_contrato.periodo_aquisitivo_meses * 30))
        }
      }
    }

    // Outras ferias aprovadas do mesmo colaborador, sobrepondo o periodo.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_solicitante.id && $db.ferias.status == "Aprovada" && $db.ferias.id != $solicitacao.id && $db.ferias.data_inicio <= $solicitacao.data_fim && $db.ferias.data_fim >= $solicitacao.data_inicio
      return = {type: "list"}
    } as $ferias_sobrepostas

    // Ausencias aprovadas do mesmo colaborador, sobrepondo o periodo.
    db.query ausencia {
      where = $db.ausencia.colaborador_id == $colaborador_solicitante.id && $db.ausencia.status == "Aprovada" && $db.ausencia.data_inicio <= $solicitacao.data_fim && $db.ausencia.data_fim >= $solicitacao.data_inicio
      return = {type: "list"}
    } as $ausencias_sobrepostas

    // Colegas do mesmo departamento ja de ferias aprovadas no mesmo periodo.
    db.query ferias {
      where = $db.ferias.status == "Aprovada" && $db.ferias.id != $solicitacao.id && $db.ferias.data_inicio <= $solicitacao.data_fim && $db.ferias.data_fim >= $solicitacao.data_inicio
      return = {type: "list"}
    } as $ferias_aprovadas_periodo

    var $colegas_de_ferias_no_periodo {
      value = 0
    }

    foreach ($ferias_aprovadas_periodo) {
      each as $ferias_periodo_item {
        db.get colaborador {
          field_name = "id"
          field_value = $ferias_periodo_item.colaborador_id
        } as $colaborador_do_periodo

        conditional {
          if ($colaborador_do_periodo != null && $colaborador_do_periodo.departamento_id == $colaborador_solicitante.departamento_id) {
            var.update $colegas_de_ferias_no_periodo {
              value = $colegas_de_ferias_no_periodo + 1
            }
          }
        }
      }
    }

    db.query colaborador {
      where = $db.colaborador.departamento_id == $colaborador_solicitante.departamento_id && $db.colaborador.status == "Ativo"
      return = {type: "list"}
    } as $equipe_do_departamento
  }

  response = {
    sucesso                      : true
    antecedencia_dias              : $antecedencia_dias
    periodo_aquisitivo_cumprido      : $periodo_aquisitivo_cumprido
    ferias_sobrepostas                 : $ferias_sobrepostas
    ausencias_sobrepostas                 : $ausencias_sobrepostas
    colegas_de_ferias_no_periodo             : $colegas_de_ferias_no_periodo
    tamanho_equipe                              : ($equipe_do_departamento|count)
  }

  guid = "conectahr-ferias-verificar-conflito-get-0001"
}
