// Consulta a resolucao de um parametro para um colaborador (item 4.11):
// aplica a ordem matriz -> norma -> instrumento coletivo -> cargo/
// departamento -> excecao individual e retorna o valor efetivo, o
// nivel resolvido e um alerta de conflito quando aplicavel. Acesso:
// RH/ADMIN, ou o proprio colaborador.
query "regras_override/resolver" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    text parametro filters=trim
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

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo != null && $colaborador_alvo.user_id == $usuario_autenticado.id)
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar esta resolucao de regra."
    }

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    precondition ($input.parametro == "horas_diarias" || $input.parametro == "horas_semanais" || $input.parametro == "intervalo_minutos" || $input.parametro == "permite_hora_extra" || $input.parametro == "limite_hora_extra_diaria" || $input.parametro == "permite_banco_horas" || $input.parametro == "prazo_compensacao_banco_horas" || $input.parametro == "controle_ponto" || $input.parametro == "dias_ferias" || $input.parametro == "permite_fracionamento" || $input.parametro == "maximo_periodos" || $input.parametro == "minimo_periodo_principal" || $input.parametro == "minimo_outros_periodos" || $input.parametro == "antecedencia_ferias" || $input.parametro == "permite_solicitacao_ferias") {
      error_type = "inputerror"
      error = "Parametro invalido."
    }

    function.run "ConectaHR/resolver_regra" {
      input = {colaborador_id: $colaborador_alvo.id, parametro: $input.parametro}
    } as $resolucao
  }

  response = {
    sucesso : true
    resolucao: $resolucao
  }

  guid = "conectahr-regras-override-resolver-get-0001"
}
