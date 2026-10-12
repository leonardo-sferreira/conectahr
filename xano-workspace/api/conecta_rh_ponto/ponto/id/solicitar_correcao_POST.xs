// Colaborador solicita a correcao de um marcador do proprio registro
// de ponto, com justificativa. O valor original e preservado no
// momento da solicitacao (Requirement: Registro de ponto e correcao).
// O horario pedido precisa ser do dia do registro, nao pode ser no futuro e respeita a
// ordem das marcacoes que ja existem (desde 11/10/2026, tarefa 78).
query "ponto/{id}/solicitar_correcao" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int id
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

    db.get registro_ponto {
      field_name = "id"
      field_value = $input.id
    } as $registro_alvo

    precondition ($registro_alvo != null) {
      error_type = "notfound"
      error = "Registro de ponto nao encontrado."
    }

    precondition ($registro_alvo.colaborador_id == $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce so pode solicitar correcao dos proprios registros de ponto."
    }

    // Valida o campo usando os valores exatos do Enum.
    precondition ($input.campo == "hora_entrada" || $input.campo == "inicio_intervalo" || $input.campo == "fim_intervalo" || $input.campo == "hora_saida") {
      error_type = "inputerror"
      error = "Campo invalido. Use hora_entrada, inicio_intervalo, fim_intervalo ou hora_saida."
    }

    // Horario pedido: dentro da janela do dia e nunca no futuro. A janela vai da meia-noite
    // UTC do dia ate as 06:00 (Brasilia) do dia seguinte, para cobrir a virada de data
    // em UTC do registro (tarefa 73) e jornadas que passam da meia-noite.
    var $inicio_janela {
      value = ($registro_alvo.data|to_timestamp)
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

        precondition ($registro_alvo.data >= $primeiro_dia_no_prazo) {
          error_type = "inputerror"
          error = "O prazo para pedir correcao deste dia acabou. Fale com o seu gestor ou com o RH, que podem ajustar."
        }
      }
    }

    // Ordem das marcacoes: entrada < saida para o almoco < volta < saida. O horario pedido
    // precisa ficar depois da marcacao anterior e antes da seguinte que ja existem.
    var $limite_inferior {
      value = null
    }

    var $limite_superior {
      value = null
    }

    conditional {
      if ($input.campo == "hora_entrada") {
        var.update $limite_superior {
          value = ($registro_alvo.inicio_intervalo != null ? $registro_alvo.inicio_intervalo : ($registro_alvo.fim_intervalo != null ? $registro_alvo.fim_intervalo : $registro_alvo.hora_saida))
        }
      }
    }

    conditional {
      if ($input.campo == "inicio_intervalo") {
        var.update $limite_inferior {
          value = $registro_alvo.hora_entrada
        }

        var.update $limite_superior {
          value = ($registro_alvo.fim_intervalo != null ? $registro_alvo.fim_intervalo : $registro_alvo.hora_saida)
        }
      }
    }

    conditional {
      if ($input.campo == "fim_intervalo") {
        var.update $limite_inferior {
          value = ($registro_alvo.inicio_intervalo != null ? $registro_alvo.inicio_intervalo : $registro_alvo.hora_entrada)
        }

        var.update $limite_superior {
          value = $registro_alvo.hora_saida
        }
      }
    }

    conditional {
      if ($input.campo == "hora_saida") {
        var.update $limite_inferior {
          value = ($registro_alvo.fim_intervalo != null ? $registro_alvo.fim_intervalo : ($registro_alvo.inicio_intervalo != null ? $registro_alvo.inicio_intervalo : $registro_alvo.hora_entrada))
        }
      }
    }

    precondition ($limite_inferior == null || $input.valor_solicitado > $limite_inferior) {
      error_type = "inputerror"
      error = "O horario pedido precisa ser depois da marcacao anterior do dia."
    }

    precondition ($limite_superior == null || $input.valor_solicitado < $limite_superior) {
      error_type = "inputerror"
      error = "O horario pedido precisa ser antes da marcacao seguinte do dia."
    }

    // Bloqueia correcao duplicada em aberto para o mesmo campo.
    db.query correcao_ponto {
      where = $db.correcao_ponto.registro_ponto_id == $registro_alvo.id && $db.correcao_ponto.campo == $input.campo && $db.correcao_ponto.status == "pendente"
      return = {type: "single"}
    } as $correcao_existente

    precondition ($correcao_existente == null) {
      error_type = "inputerror"
      error = "Ja existe uma solicitacao de correcao pendente para este campo."
    }

    // Le o valor original do campo indicado (nao ha campo dinamico em XanoScript).
    var $valor_original_atual {
      value = null
    }

    conditional {
      if ($input.campo == "hora_entrada") {
        var.update $valor_original_atual {
          value = $registro_alvo.hora_entrada
        }
      }
    }

    conditional {
      if ($input.campo == "inicio_intervalo") {
        var.update $valor_original_atual {
          value = $registro_alvo.inicio_intervalo
        }
      }
    }

    conditional {
      if ($input.campo == "fim_intervalo") {
        var.update $valor_original_atual {
          value = $registro_alvo.fim_intervalo
        }
      }
    }

    conditional {
      if ($input.campo == "hora_saida") {
        var.update $valor_original_atual {
          value = $registro_alvo.hora_saida
        }
      }
    }

    db.add correcao_ponto {
      data = {
        registro_ponto_id : $registro_alvo.id
        colaborador_id     : $colaborador_autenticado.id
        campo               : $input.campo
        valor_original       : $valor_original_atual
        valor_solicitado      : $input.valor_solicitado
        justificativa          : $input.justificativa
        status                  : "pendente"
        updated_at               : "now"
      }
    } as $correcao_criada

    // Auditoria: solicitacao de correcao de ponto.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "solicitar_correcao_ponto"
        recurso    : "correcao_ponto"
        registro_id: $correcao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Solicitacao de correcao registrada com sucesso."
    correcao : $correcao_criada
  }

  guid = "conectahr-ponto-solicitar-correcao-post-0001"
}
