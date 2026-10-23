// Termometro de humor da propria pessoa (change termometro-de-humor, D3): o ciclo de 10 dias de hoje (ciclo 0 =
// 21/10/2026 a 30/10/2026) e se ela ja respondeu. Tambem dispara os convites de pesquisa pendentes
// (change notificacoes-de-publicacao, D3). Qualquer perfil com ficha.
query "humor" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    var $ano {
      value = ($hoje|substr:0:4)|to_int
    }

    var $mes {
      value = ($hoje|substr:5:2)|to_int
    }

    var $dia {
      value = ($hoje|substr:8:2)|to_int
    }

    var $a_jd {
      value = ((14 - $mes) / 12)|floor
    }

    var $y_jd {
      value = $ano + 4800 - $a_jd
    }

    var $m_jd {
      value = $mes + (12 * $a_jd) - 3
    }

    var $parte_mes {
      value = (((153 * $m_jd) + 2) / 5)|floor
    }

    var $bissextos {
      value = (($y_jd / 4)|floor) - (($y_jd / 100)|floor) + (($y_jd / 400)|floor)
    }

    var $dia_juliano {
      value = $dia + $parte_mes + (365 * $y_jd) + $bissextos - 32045
    }

    var $ciclo {
      value = (($dia_juliano - 2461335) / 10)|floor
    }

    // Convites pendentes saem no primeiro acesso ao Inicio do dia (change notificacoes-de-publicacao, D3).
    function.run "ConectaHR/enviar_convites_pesquisa" {
      input = {aplicar: true, autor_user_id: null, incluir_termometro: true}
    } as $convites_pendentes

    db.query humor_participacao {
      where = $db.humor_participacao.ciclo == $ciclo && $db.humor_participacao.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $participacao
  }

  response = {
    sucesso  : true
    hoje     : $hoje
    ciclo    : $ciclo
    respondeu: $participacao != null
  }

  guid = "conectahr-humor-get-0001"
}
