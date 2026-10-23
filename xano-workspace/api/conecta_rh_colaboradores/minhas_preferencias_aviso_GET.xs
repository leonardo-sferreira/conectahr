// Preferencias de aviso da pessoa autenticada, por assunto e canal (change
// configuracoes-seguranca-notificacoes, D2). Sem registro, os dois canais vem ligados (padrao nao
// gravado). Beneficios, alertas de seguranca e pedidos para decidir nao aparecem: sao sempre entregues.
query "minhas_preferencias_aviso" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    var $assuntos {
      value = ["ferias_ausencias", "ponto", "documentos", "avaliacoes_metas", "solicitacoes", "treinamentos", "pesquisas"]
    }

    var $preferencias {
      value = []
    }

    foreach ($assuntos) {
      each as $assunto_item {
        db.query preferencia_aviso {
          where = $db.preferencia_aviso.user_id == $usuario_autenticado.id && $db.preferencia_aviso.assunto == $assunto_item
          return = {type: "single"}
        } as $preferencia_existente

        var.update $preferencias {
          value = $preferencias|push:{assunto: $assunto_item, plataforma: ($preferencia_existente != null ? $preferencia_existente.plataforma : true), email: ($preferencia_existente != null ? $preferencia_existente.email : true)}
        }
      }
    }
  }

  response = {
    sucesso     : true
    preferencias: $preferencias
  }

  guid = "conectahr-minhas-preferencias-aviso-get-0001"
}
