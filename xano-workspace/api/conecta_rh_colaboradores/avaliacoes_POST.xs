// RH/ADMIN atribui uma avaliacao: quem avalia (user_id) avalia quem
// (colaborador_id), dentro de um ciclo, com a relacao entre eles
// (autoavaliacao, gestor, par, subordinado, rh).
query avaliacoes verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    int user_id
    int ciclo_avaliacao_id
    text relacao_avaliador filters=trim
    date? periodo_incio?
    date? periodo_fim?
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem atribuir avaliacoes."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_avaliado

    precondition ($colaborador_avaliado != null) {
      error_type = "notfound"
      error = "Colaborador avaliado nao encontrado."
    }

    db.get user {
      field_name = "id"
      field_value = $input.user_id
    } as $usuario_avaliador

    precondition ($usuario_avaliador != null) {
      error_type = "notfound"
      error = "Avaliador nao encontrado."
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.ciclo_avaliacao_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    // Valida a relacao usando os valores exatos do Enum.
    precondition ($input.relacao_avaliador == "autoavaliacao" || $input.relacao_avaliador == "gestor" || $input.relacao_avaliador == "par" || $input.relacao_avaliador == "subordinado" || $input.relacao_avaliador == "rh") {
      error_type = "inputerror"
      error = "Relacao invalida. Use autoavaliacao, gestor, par, subordinado ou rh."
    }

    // Autoavaliacao exige que o avaliador seja o proprio colaborador.
    precondition ($input.relacao_avaliador != "autoavaliacao" || $colaborador_avaliado.user_id == $usuario_avaliador.id) {
      error_type = "inputerror"
      error = "Em autoavaliacao, o avaliador precisa ser a conta do proprio colaborador."
    }

    db.add avaliacao {
      data = {
        colaborador_id      : $colaborador_avaliado.id
        user_id                : $usuario_avaliador.id
        ciclo_avaliacao_id        : $ciclo.id
        relacao_avaliador            : $input.relacao_avaliador
        periodo_incio                   : $input.periodo_incio
        periodo_fim                        : $input.periodo_fim
        status                               : "pendente"
        updated_at                              : "now"
      }
    } as $avaliacao_criada

    // Auditoria: atribuicao de avaliacao.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "atribuir_avaliacao"
        recurso    : "avaliacao"
        registro_id: $avaliacao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    // Notificacao interna + outbox de e-mail (itens 5.5/5.6/5.11) para
    // o avaliador — a avaliacao ficou disponivel para ser preenchida.
    db.add notificacao_interna {
      data = {
        destinatario_user_id: $usuario_avaliador.id
        tipo                : "avaliacao_disponivel"
        titulo              : "Avaliacao disponivel"
        mensagem            : "Uma avaliacao foi atribuida a voce. Acesse o sistema para preenche-la."
        recurso             : "avaliacao"
        registro_id         : $avaliacao_criada.id
      }
    } as $notificacao_avaliacao_criada

    db.add email_outbox {
      data = {
        destinatario_email : $usuario_avaliador.email
        destinatario_nome  : $usuario_avaliador.nome
        assunto            : "ConectaRH - Avaliacao disponivel"
        corpo              : "Ola " ~ $usuario_avaliador.nome ~ ",\n\nUma avaliacao foi atribuida a voce no ConectaRH. Acesse o sistema para preenche-la.\n\nEste e um aviso automatico."
        chave_idempotencia : ("avaliacao_disponivel_" ~ ($avaliacao_criada.id|to_text))
      }
    } as $outbox_avaliacao_criado
  }

  response = {
    sucesso   : true
    mensagem  : "Avaliacao atribuida com sucesso."
    avaliacao : $avaliacao_criada
  }

  guid = "conectahr-avaliacoes-post-0001"
}
