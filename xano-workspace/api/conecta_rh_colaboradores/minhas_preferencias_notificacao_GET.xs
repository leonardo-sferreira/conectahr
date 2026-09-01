// Preferencias de notificacao do usuario autenticado (item 7.8). So
// cobre eventos nao-criticos configuraveis; alertas obrigatorios de
// seguranca (codigo de acesso de login, redefinicao de senha, alerta de
// acesso suspeito) nunca aparecem aqui e continuam sempre enviados,
// porque nao existem como valor do enum tipo_evento — bloqueado por
// design, nao so por checagem em runtime. Quando o usuario nunca
// configurou um tipo, o padrao retornado (nao persistido) e canal_email
// ativo e frequencia imediata.
query "minhas_preferencias_notificacao" verb=GET {
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

    var $tipos_evento {
      value = ["documento_vencendo", "solicitacao_respondida", "avaliacao_disponivel", "ferias_aprovada", "documento_pendente"]
    }

    var $tipos_obrigatorios {
      value = ["codigo_acesso_login", "redefinicao_senha", "alerta_acesso_suspeito"]
    }

    var $preferencias {
      value = []
    }

    foreach ($tipos_evento) {
      each as $tipo_item {
        db.query preferencia_notificacao {
          where = $db.preferencia_notificacao.user_id == $usuario_autenticado.id && $db.preferencia_notificacao.tipo_evento == $tipo_item
          return = {type: "single"}
        } as $preferencia_existente

        var $item_canal_email {
          value = ($preferencia_existente != null ? $preferencia_existente.canal_email : true)
        }

        var $item_frequencia {
          value = ($preferencia_existente != null ? $preferencia_existente.frequencia : "imediato")
        }

        var.update $preferencias {
          value = ($preferencias|push:{tipo_evento: $tipo_item, canal_email: $item_canal_email, frequencia: $item_frequencia})
        }
      }
    }
  }

  response = {
    sucesso                            : true
    preferencias                       : $preferencias
    tipos_obrigatorios_nao_desativaveis: $tipos_obrigatorios
  }

  guid = "conectahr-minhas-preferencias-notificacao-get-0001"
}
