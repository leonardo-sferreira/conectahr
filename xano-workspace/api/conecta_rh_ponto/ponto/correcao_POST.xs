// Pedido de correcao de ponto do proprio colaborador no REP-P (change ponto-rep-p-e-ferias-clt):
// incluir uma marcacao que faltou ou desconsiderar uma marcacao feita por engano, com motivo.
// A marcacao original nunca e alterada: aprovado, o pedido vira um tratamento
// (correcoes_ponto/{id}/aprovar). Vale para dia com ou sem marcacao, do dia da admissao ate
// hoje, dentro do prazo definido pelo RH. Substitui ponto/{id}/solicitar_correcao e
// ponto/solicitar_correcao_dia.
query "ponto/correcao" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    date data
    enum tipo {
      values = ["inclusao", "desconsideracao"]
    }

    int? marcacao_id?
    timestamp? data_hora?
    text justificativa filters=trim|min:5|max:150
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

    precondition (($colaborador_autenticado.status|trim|to_upper) != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode pedir correcao de ponto."
    }

    var $hoje_brasilia {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $dia {
      value = $input.data|format_timestamp:"Y-m-d":"UTC"
    }

    precondition ($dia <= $hoje_brasilia) {
      error_type = "inputerror"
      error = "Nao e possivel corrigir um dia futuro."
    }

    precondition ($colaborador_autenticado.data_admissao == null || $dia >= ($colaborador_autenticado.data_admissao|format_timestamp:"Y-m-d":"UTC")) {
      error_type = "inputerror"
      error = "O dia e anterior a admissao."
    }

    function.run "ConectaHR/validar_tratamento" {
      input = {colaborador_id: $colaborador_autenticado.id, data: $dia, tipo: $input.tipo, marcacao_id: $input.marcacao_id, data_hora: $input.data_hora}
    } as $validacao

    // Garante o registro do dia (cache), ao qual o pedido fica ligado.
    function.run "ConectaHR/atualizar_dia_ponto" {
      input = {colaborador_id: $colaborador_autenticado.id, data: $dia}
    } as $dia_atual

    // Prazo para pedir correcao (tarefa 79), definido pelo RH em ponto/prazo_correcao.
    db.query configuracao {
      where = $db.configuracao.chave == "prazo_correcao_ponto_dias"
      return = {type: "single"}
    } as $config_prazo

    conditional {
      if ($config_prazo != null && $config_prazo.valor_inteiro != null) {
        precondition ($dia >= ((now|add_secs_to_timestamp:(0 - $config_prazo.valor_inteiro * 86400))|format_timestamp:"Y-m-d":"America/Sao_Paulo")) {
          error_type = "inputerror"
          error = "O prazo para pedir correcao deste dia acabou. Fale com o seu gestor ou com o RH, que podem ajustar."
        }
      }
    }

    // Desconsideracao: o horario da marcacao fica em valor_original, para quem decide ver o dia e a hora.
    var $momento_original {
      value = null
    }

    conditional {
      if ($input.tipo == "desconsideracao") {
        db.get marcacao_ponto {
          field_name = "id"
          field_value = $input.marcacao_id
        } as $marcacao_alvo

        var.update $momento_original {
          value = $marcacao_alvo.data_hora_marcacao
        }
      }
    }

    db.add correcao_ponto {
      data = {
        registro_ponto_id: $dia_atual.registro.id
        colaborador_id   : $colaborador_autenticado.id
        tipo             : $input.tipo
        marcacao_id      : $input.marcacao_id
        valor_solicitado : ($input.tipo == "inclusao" ? $input.data_hora : null)
        valor_original   : $momento_original
        justificativa    : $input.justificativa
        status           : "pendente"
        updated_at       : "now"
      }
    } as $correcao_criada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "solicitar_correcao_ponto"
        recurso    : "correcao_ponto"
        registro_id: $correcao_criada.id
        valor_novo : "tipo=" ~ $input.tipo ~ "; dia=" ~ $dia
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Pedido de correcao enviado."
    correcao: $correcao_criada
  }

  guid = "conectahr-ponto-correcao-post-0001"
}
