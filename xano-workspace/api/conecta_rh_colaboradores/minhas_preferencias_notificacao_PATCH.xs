// Atualiza a preferencia de canal/frequencia de um tipo de evento
// nao-critico (item 7.8). canal_email e frequencia sao obrigatorios
// (nao opcionais) de proposito: campos bool/text opcionais tem um
// quirk confirmado nesta plataforma onde false/"" sao coercidos para
// null em comparacoes == / != (ver conectahr-xano-platform-quirks,
// achado 19) — se canal_email fosse opcional, um PATCH explicito para
// desativar o e-mail (canal_email=false) poderia ser tratado como "nao
// informado" e silenciosamente ignorado. Exigir os dois campos sempre
// evita essa ambiguidade por completo.
query "minhas_preferencias_notificacao" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text tipo_evento filters=trim
    bool canal_email
    text frequencia filters=trim
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

    // Lista fechada e proposital: alertas obrigatorios de seguranca
    // nunca sao um valor aceito aqui, entao nunca podem ser desativados
    // por este endpoint.
    precondition ($input.tipo_evento == "documento_vencendo" || $input.tipo_evento == "solicitacao_respondida" || $input.tipo_evento == "avaliacao_disponivel" || $input.tipo_evento == "ferias_aprovada" || $input.tipo_evento == "documento_pendente") {
      error_type = "inputerror"
      error = "Tipo de evento invalido ou nao configuravel. Alertas obrigatorios de seguranca (codigo de acesso, redefinicao de senha, acesso suspeito) nao podem ser desativados."
    }

    precondition ($input.frequencia == "imediato" || $input.frequencia == "resumo_diario" || $input.frequencia == "resumo_semanal") {
      error_type = "inputerror"
      error = "Frequencia invalida. Use imediato, resumo_diario ou resumo_semanal."
    }

    db.query preferencia_notificacao {
      where = $db.preferencia_notificacao.user_id == $usuario_autenticado.id && $db.preferencia_notificacao.tipo_evento == $input.tipo_evento
      return = {type: "single"}
    } as $preferencia_existente

    conditional {
      if ($preferencia_existente == null) {
        db.add preferencia_notificacao {
          data = {
            user_id     : $usuario_autenticado.id
            tipo_evento : $input.tipo_evento
            canal_email : $input.canal_email
            frequencia  : $input.frequencia
          }
        } as $preferencia_criada
      }
    }

    conditional {
      if ($preferencia_existente != null) {
        db.edit preferencia_notificacao {
          field_name = "id"
          field_value = $preferencia_existente.id
          data = {
            canal_email: $input.canal_email
            frequencia : $input.frequencia
            updated_at : "now"
          }
        } as $preferencia_atualizada
      }
    }

    // Auditoria: alteracao de preferencia de notificacao.
    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "atualizar_preferencia_notificacao"
        recurso      : "preferencia_notificacao"
        justificativa: ("tipo_evento=" ~ $input.tipo_evento ~ " canal_email=" ~ ($input.canal_email|to_text) ~ " frequencia=" ~ $input.frequencia)
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    tipo_evento: $input.tipo_evento
    canal_email: $input.canal_email
    frequencia : $input.frequencia
  }

  guid = "conectahr-minhas-preferencias-notificacao-patch-0001"
}
