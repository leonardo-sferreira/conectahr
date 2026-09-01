// Aprova uma solicitacao de ferias.
// Operacao permitida somente para RH ou ADMIN.
// Nao altera o periodo solicitado.
query "ferias/{id}/aprovar" verb=POST {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_decisor
  
    precondition ($usuario_decisor != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }
  
    // Contas inativas nao podem aprovar ferias.
    precondition ($usuario_decisor.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_decisor.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_decisor {
      value = $usuario_decisor.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem aprovar.
    precondition ($perfil_decisor == "RH" || $perfil_decisor == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem aprovar solicitacoes de ferias."
    }
  
    // Localiza a solicitacao.
    db.get ferias {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao
  
    precondition ($solicitacao != null) {
      error_type = "notfound"
      error = "Solicitacao de ferias nao encontrada."
    }
  
    // Normaliza o status atual.
    var $status_solicitacao {
      value = $solicitacao.status|trim|to_upper
    }
  
    // Somente solicitacoes pendentes podem ser aprovadas.
    precondition ($status_solicitacao == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente solicitacoes pendentes podem ser aprovadas."
    }
  
    // Localiza o colaborador relacionado.
    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador relacionado a solicitacao nao encontrado."
    }
  
    // O colaborador precisa continuar ativo.
    var $status_colaborador {
      value = $colaborador.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "inputerror"
      error = "Nao e possivel aprovar ferias para um colaborador inativo ou desligado."
    }
  
    // Registra a decisao.
    db.edit ferias {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        status              : "Aprovada"
        decidido_por_user_id: $usuario_decisor.id
        data_decisao        : "now"
        updated_at          : "now"
      }
    } as $solicitacao_aprovada

    // Auditoria: decisao de aprovacao de ferias.
    db.add auditoria {
      data = {
        user_id       : $usuario_decisor.id
        acao          : "aprovar_ferias"
        recurso       : "ferias"
        registro_id   : $solicitacao.id
        resultado     : "sucesso"
      }
    } as $evento_auditoria

    // Notificacao interna + outbox de e-mail (itens 5.5/5.6/5.11) —
    // criadas juntas, no mesmo evento que dispara o aviso ao colaborador.
    conditional {
      if ($colaborador.user_id != null) {
        db.get user {
          field_name = "id"
          field_value = $colaborador.user_id
        } as $conta_colaborador_notificar

        conditional {
          if ($conta_colaborador_notificar != null) {
            db.add notificacao_interna {
              data = {
                destinatario_user_id: $conta_colaborador_notificar.id
                tipo                : "ferias_aprovada"
                titulo              : "Ferias aprovadas"
                mensagem            : "Sua solicitacao de ferias foi aprovada. Consulte o periodo no sistema."
                recurso             : "ferias"
                registro_id         : $solicitacao.id
              }
            } as $notificacao_criada

            // Preferencia de notificacao (item 7.8): notificacao interna
            // acima e sempre criada; o e-mail respeita a preferencia de
            // canal do colaborador, com padrao ativo quando nunca configurada.
            db.query preferencia_notificacao {
              where = $db.preferencia_notificacao.user_id == $conta_colaborador_notificar.id && $db.preferencia_notificacao.tipo_evento == "ferias_aprovada"
              return = {type: "single"}
            } as $preferencia_ferias_aprovada

            var $enviar_email_ferias_aprovada {
              value = ($preferencia_ferias_aprovada != null ? $preferencia_ferias_aprovada.canal_email : true)
            }

            conditional {
              if ($enviar_email_ferias_aprovada) {
                db.add email_outbox {
                  data = {
                    destinatario_email   : $conta_colaborador_notificar.email
                    destinatario_nome    : $conta_colaborador_notificar.nome
                    assunto              : "ConectaRH - Ferias aprovadas"
                    corpo                : "Ola " ~ $conta_colaborador_notificar.nome ~ ",\n\nSua solicitacao de ferias foi aprovada. Acesse o ConectaRH para ver o periodo.\n\nEste e um aviso automatico."
                    chave_idempotencia   : ("ferias_aprovada_" ~ ($solicitacao.id|to_text))
                  }
                } as $outbox_criado
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao de ferias aprovada com sucesso."
    solicitacao: $solicitacao_aprovada
  }

  guid = "qvoahcUiJoVjcVuBWT4z_rgIqdM"
}