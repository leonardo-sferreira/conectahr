// Fila de e-mails para a tela "Integracoes e e-mails" (Admin; change integracoes-e-emails, D1; Figma 249:7847).
// Os 50 mais recentes (todos ou de uma situacao: pendente, enviado, falhou), com o assunto, o tipo (a chave de
// idempotencia sem os numeros), o destinatario mascarado (primeira letra e o dominio: o e-mail inteiro nao sai
// daqui), as tentativas, o ultimo erro e as datas; e as contagens: na fila (pendentes), enviados e falharam nas
// ultimas 24 horas. O corpo do e-mail nao sai. So RH e Admin, como `email_outbox/processar`.
query "email_outbox" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text? status? filters=trim|lower
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    var $status_filtro {
      value = (($input.status == null) || ($input.status == "")) ? "" : $input.status
    }

    precondition (($status_filtro == "") || ($status_filtro == "pendente") || ($status_filtro == "enviado") || ($status_filtro == "falhou")) {
      error_type = "inputerror"
      error = "Situacao invalida. Use pendente, enviado ou falhou."
    }

    var $limite_24h {
      value = now|add_secs_to_timestamp:-86400
    }

    db.query email_outbox {
      where = $db.email_outbox.status == "pendente"
      return = {type: "count"}
    } as $na_fila

    db.query email_outbox {
      where = $db.email_outbox.status == "enviado" && $db.email_outbox.enviado_em >= $limite_24h
      return = {type: "count"}
    } as $enviados_24h

    db.query email_outbox {
      where = $db.email_outbox.status == "falhou" && $db.email_outbox.updated_at >= $limite_24h
      return = {type: "count"}
    } as $falharam_24h

    db.query email_outbox {
      sort = {email_outbox.created_at: "desc"}
      return = {type: "list"}
    } as $todos

    var $itens {
      value = []
    }

    foreach ($todos) {
      each as $e {
        conditional {
          if ((($status_filtro == "") || ($e.status == $status_filtro)) && (($itens|count) < 50)) {
            var $partes_email {
              value = $e.destinatario_email|split:"@"
            }

            var $usuario_email {
              value = $partes_email|first
            }

            var $mascarado {
              value = ($usuario_email|substr:0:1) ~ "***@" ~ ($partes_email|last)
            }

            var.update $itens {
              value = $itens|push:{
                id            : $e.id
                assunto       : $e.assunto
                chave         : $e.chave_idempotencia
                destinatario  : $mascarado
                status        : $e.status
                tentativas    : $e.tentativas
                max_tentativas: $e.max_tentativas
                ultimo_erro   : $e.ultimo_erro
                criado_em     : $e.created_at
                enviado_em    : $e.enviado_em
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso     : true
    contagens   : {na_fila: $na_fila, enviados_24h: $enviados_24h, falharam_24h: $falharam_24h}
    emails      : $itens
  }

  guid = "conectahr-email-outbox-get-0001"
}
