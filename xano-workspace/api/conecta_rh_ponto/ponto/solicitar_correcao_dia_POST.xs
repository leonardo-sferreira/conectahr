// Colaborador pede a correcao de um dia em que nao marcou ponto nenhuma vez (tarefa 78).
// Sem registro nao ha como usar ponto/{id}/solicitar_correcao: este endpoint cria o registro
// do dia (status Incompleto, sem marcacoes) e o pedido de correcao do campo informado. Os
// outros campos do dia seguem pelo endpoint normal, com o id devolvido.
// Regras: so o proprio colaborador, nao desligado; so dia passado (em Brasilia), nao antes da
// admissao e sem registro existente; horario dentro da janela do dia e nunca no futuro.
// Quem decide e o gestor ou o RH, como nas outras correcoes.
query "ponto/solicitar_correcao_dia" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    date data
    text campo filters=trim
    timestamp valor_solicitado
    text justificativa filters=trim|min:5|max:1000
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
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode pedir correcao de ponto."
    }

    precondition ($input.campo == "hora_entrada" || $input.campo == "inicio_intervalo" || $input.campo == "fim_intervalo" || $input.campo == "hora_saida") {
      error_type = "inputerror"
      error = "Campo invalido. Use hora_entrada, inicio_intervalo, fim_intervalo ou hora_saida."
    }

    // So dia passado, no horario de Brasilia: o dia de hoje se marca pelo ponto/marcar.
    var $hoje_brasilia {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition ($input.data < $hoje_brasilia) {
      error_type = "inputerror"
      error = "So e possivel pedir correcao de um dia que ja passou. Hoje, use Marcar agora."
    }

    precondition ($colaborador_autenticado.data_admissao == null || $input.data >= $colaborador_autenticado.data_admissao) {
      error_type = "inputerror"
      error = "O dia pedido e anterior a sua admissao."
    }

    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colaborador_autenticado.id && $db.registro_ponto.data == $input.data
      return = {type: "single"}
    } as $registro_do_dia

    precondition ($registro_do_dia == null) {
      error_type = "inputerror"
      error = "Ja existe registro neste dia: peca a correcao pelo registro."
    }

    // Horario pedido: dentro da janela do dia e nunca no futuro. A janela vai da meia-noite
    // UTC do dia ate as 06:00 (Brasilia) do dia seguinte, para cobrir a virada de data
    // em UTC do registro (tarefa 73) e jornadas que passam da meia-noite.
    var $inicio_janela {
      value = ($input.data|to_timestamp)
    }

    var $fim_janela {
      value = $inicio_janela + 86400000 + 32400000
    }

    precondition ($input.valor_solicitado >= $inicio_janela && $input.valor_solicitado <= $fim_janela) {
      error_type = "inputerror"
      error = "O horario pedido precisa ser do mesmo dia do registro."
    }

    precondition ($input.valor_solicitado <= now) {
      error_type = "inputerror"
      error = "O horario pedido nao pode ser no futuro."
    }

    // Prazo para pedir correcao (tarefa 83), definido pelo RH em ponto/prazo_correcao.
    db.query configuracao {
      where = $db.configuracao.chave == "prazo_correcao_ponto_dias"
      return = {type: "single"}
    } as $config_prazo

    conditional {
      if ($config_prazo != null && $config_prazo.valor_inteiro != null) {
        var $primeiro_dia_no_prazo {
          value = (now - ($config_prazo.valor_inteiro * 86400000))|format_timestamp:"Y-m-d":"America/Sao_Paulo"
        }

        precondition ($input.data >= $primeiro_dia_no_prazo) {
          error_type = "inputerror"
          error = "O prazo para pedir correcao deste dia acabou. Fale com o seu gestor ou com o RH, que podem ajustar."
        }
      }
    }

    db.add registro_ponto {
      data = {
        colaborador_id: $colaborador_autenticado.id
        data          : $input.data
        status        : "Incompleto"
        observacao    : "Criado por pedido de correcao (dia sem marcacao)."
        updated_at    : "now"
      }
    } as $registro_criado

    db.add correcao_ponto {
      data = {
        registro_ponto_id : $registro_criado.id
        colaborador_id     : $colaborador_autenticado.id
        campo               : $input.campo
        valor_original       : null
        valor_solicitado      : $input.valor_solicitado
        justificativa          : $input.justificativa
        status                  : "pendente"
        updated_at               : "now"
      }
    } as $correcao_criada

    // Auditoria: pedido de correcao de um dia sem marcacao.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "solicitar_correcao_ponto_dia"
        recurso    : "correcao_ponto"
        registro_id: $correcao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Pedido de correcao registrado. O dia aparece no espelho como incompleto ate a decisao."
    registro_id: $registro_criado.id
    correcao   : $correcao_criada
  }

  guid = "conectahr-ponto-solicitar-correcao-dia-post-0001"
}
