// Resolve um parametro para um colaborador e persiste a regra aplicada
// (item 4.12) — grava regra_contrato/regra_override/instrumento_
// normativo de origem, versao, parametros e data do calculo, associados
// a um processo (ex.: "ferias", processo_id = id da solicitacao).
// Bloqueia quando a resolucao encontra conflito nao resolvido (spec.md
// - "Conflito juridico"): nesse caso exige analise humana antes de
// aplicar. Operacao de RH/ADMIN.
query "regras_override/aplicar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    text parametro filters=trim
    text processo_tipo filters=trim|max:50
    int processo_id
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem aplicar e persistir regras."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    function.run "ConectaHR/resolver_regra" {
      input = {colaborador_id: $colaborador_alvo.id, parametro: $input.parametro}
    } as $resolucao

    // Conflito nao resolvido bloqueia a aplicacao e exige analise humana.
    precondition ($resolucao.conflito == false) {
      error_type = "accessdenied"
      error = "Ha um conflito entre regras vigentes de mesma prioridade e especificidade para este parametro. Resolva manualmente antes de aplicar."
    }

    var $override_id_aplicado {
      value = ($resolucao.override_aplicado != null ? $resolucao.override_aplicado.id : null)
    }

    var $instrumento_id_aplicado {
      value = ($resolucao.override_aplicado != null ? $resolucao.override_aplicado.instrumento_normativo_id : null)
    }

    var $versao_aplicada {
      value = ($resolucao.override_aplicado != null ? ($resolucao.override_aplicado.versao|to_text) : "matriz")
    }

    var $parametros_aplicados_json {
      value = {
        parametro       : $input.parametro
        nivel_resolvido : $resolucao.nivel_resolvido
        valor_matriz    : ($resolucao.regra_contrato != null ? $resolucao.regra_contrato.id : null)
        valor_override  : ($resolucao.override_aplicado != null ? $resolucao.override_aplicado.valor_novo : null)
      }
    }

    db.add regra_aplicada {
      data = {
        colaborador_id       : $colaborador_alvo.id
        regra_contrato_id    : $resolucao.regra_contrato_id
        regra_override_id    : $override_id_aplicado
        instrumento_normativo_id: $instrumento_id_aplicado
        processo_tipo         : $input.processo_tipo
        processo_id            : $input.processo_id
        regra_aplicada_versao     : $versao_aplicada
        parametros_aplicados        : $parametros_aplicados_json
        data_calculo                   : "now"
      }
    } as $regra_aplicada_criada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "aplicar_regra_resolvida"
        recurso    : "regra_aplicada"
        registro_id: $regra_aplicada_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso       : true
    mensagem      : "Regra resolvida e aplicada persistida com sucesso."
    resolucao     : $resolucao
    regra_aplicada: $regra_aplicada_criada
  }

  guid = "conectahr-regras-override-aplicar-post-0001"
}
