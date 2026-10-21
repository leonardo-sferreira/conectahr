// Atualiza uma acao do plano de riscos psicossociais (change riscos-psicossociais, D3): a situacao e, se vierem,
// a medida, o responsavel e o prazo. Concluir grava a data. Auditado com a situacao anterior e a nova. So RH e Admin.
query "acoes_psicossociais/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text status filters=trim|lower
    text? medida? filters=trim|max:1000
    text? responsavel? filters=trim|max:150
    date? prazo?
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

    db.get acao_psicossocial {
      field_name = "id"
      field_value = $input.id
    } as $acao

    precondition ($acao != null) {
      error_type = "notfound"
      error = "Acao nao encontrada."
    }

    precondition (($input.status == "planejada") || ($input.status == "em_andamento") || ($input.status == "concluida") || ($input.status == "cancelada")) {
      error_type = "inputerror"
      error = "Situacao invalida. Use planejada, em_andamento, concluida ou cancelada."
    }

    var $medida {
      value = (($input.medida == null) || ($input.medida == "")) ? $acao.medida : $input.medida
    }

    var $responsavel {
      value = (($input.responsavel == null) || ($input.responsavel == "")) ? $acao.responsavel : $input.responsavel
    }

    var $prazo {
      value = ($input.prazo == null) ? $acao.prazo : $input.prazo
    }

    var $concluida_em {
      value = ($input.status == "concluida") ? (($acao.concluida_em != null) ? $acao.concluida_em : $hoje) : null
    }

    db.edit acao_psicossocial {
      field_name = "id"
      field_value = $acao.id
      data = {status: $input.status, medida: $medida, responsavel: $responsavel, prazo: $prazo, concluida_em: $concluida_em, updated_at: "now"}
    } as $acao_atualizada

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "atualizar_acao_psicossocial"
        recurso      : "acao_psicossocial"
        registro_id  : $acao.id
        resultado    : "sucesso"
        justificativa: ($acao.status ~ " -> " ~ $input.status)
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Acao atualizada."
    acao    : $acao_atualizada
  }

  guid = "conectahr-acoes-psicossociais-id-patch-0001"
}
