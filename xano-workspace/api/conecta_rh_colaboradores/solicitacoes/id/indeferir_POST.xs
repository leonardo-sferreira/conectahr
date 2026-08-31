// RH/ADMIN indefere uma solicitacao, com justificativa obrigatoria.
query "solicitacoes/{id}/indeferir" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text justificativa_decisao filters=trim|min:5|max:1000
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
      error = "Somente RH ou ADMIN podem decidir solicitacoes."
    }

    db.get solicitacao_rh {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao_atual

    precondition ($solicitacao_atual != null) {
      error_type = "notfound"
      error = "Solicitacao nao encontrada."
    }

    precondition ($solicitacao_atual.status == "recebida" || $solicitacao_atual.status == "em_analise") {
      error_type = "inputerror"
      error = "Somente solicitacoes recebidas ou em analise podem ser indeferidas."
    }

    db.edit solicitacao_rh {
      field_name = "id"
      field_value = $solicitacao_atual.id
      data = {
        status                : "indeferida"
        decidido_por_user_id  : $usuario_autenticado.id
        justificativa_decisao : $input.justificativa_decisao
        data_decisao           : "now"
        updated_at              : "now"
      }
    } as $solicitacao_indeferida

    // Auditoria: decisao de indeferimento.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "indeferir_solicitacao_rh"
        recurso       : "solicitacao_rh"
        registro_id   : $solicitacao_atual.id
        justificativa : $input.justificativa_decisao
        resultado     : "sucesso"
      }
    } as $evento_auditoria

    // Notificacao interna + outbox de e-mail (itens 5.5/5.6/5.11) para
    // quem fez a solicitacao.
    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao_atual.colaborador_id
    } as $colaborador_solicitante_indeferir

    conditional {
      if ($colaborador_solicitante_indeferir != null && $colaborador_solicitante_indeferir.user_id != null) {
        db.get user {
          field_name = "id"
          field_value = $colaborador_solicitante_indeferir.user_id
        } as $conta_solicitante_indeferir

        conditional {
          if ($conta_solicitante_indeferir != null) {
            db.add notificacao_interna {
              data = {
                destinatario_user_id: $conta_solicitante_indeferir.id
                tipo                : "solicitacao_respondida"
                titulo              : "Solicitacao indeferida"
                mensagem            : "Sua solicitacao ao RH foi indeferida. Acesse o sistema para ver o motivo."
                recurso             : "solicitacao_rh"
                registro_id         : $solicitacao_atual.id
              }
            } as $notificacao_indeferir_criada

            db.add email_outbox {
              data = {
                destinatario_email : $conta_solicitante_indeferir.email
                destinatario_nome  : $conta_solicitante_indeferir.nome
                assunto            : "ConectaRH - Solicitacao indeferida"
                corpo              : "Ola " ~ $conta_solicitante_indeferir.nome ~ ",\n\nSua solicitacao ao RH foi indeferida. Acesse o ConectaRH para ver o motivo.\n\nEste e um aviso automatico."
                chave_idempotencia : ("solicitacao_respondida_" ~ ($solicitacao_atual.id|to_text))
              }
            } as $outbox_indeferir_criado
          }
        }
      }
    }
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao indeferida."
    solicitacao: $solicitacao_indeferida
  }

  guid = "conectahr-solicitacoes-indeferir-post-0001"
}
