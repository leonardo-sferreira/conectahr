// Grava a preferencia de aviso de um assunto (change configuracoes-seguranca-notificacoes, D2).
// plataforma e email sao obrigatorios (bool opcional vira nulo em comparacao nesta plataforma).
// Assuntos sempre ligados (beneficios, seguranca) nao sao aceitos. Auditado.
query "minhas_preferencias_aviso" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text assunto filters=trim
    bool plataforma
    bool email
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

    precondition (($input.assunto == "ferias_ausencias") || ($input.assunto == "ponto") || ($input.assunto == "documentos") || ($input.assunto == "avaliacoes_metas") || ($input.assunto == "solicitacoes") || ($input.assunto == "treinamentos") || ($input.assunto == "pesquisas")) {
      error_type = "inputerror"
      error = "Assunto invalido ou sempre ligado. Avisos de beneficios e alertas de seguranca nao podem ser desligados."
    }

    db.query preferencia_aviso {
      where = $db.preferencia_aviso.user_id == $usuario_autenticado.id && $db.preferencia_aviso.assunto == $input.assunto
      return = {type: "single"}
    } as $preferencia_existente

    conditional {
      if ($preferencia_existente == null) {
        db.add preferencia_aviso {
          data = {user_id: $usuario_autenticado.id, assunto: $input.assunto, plataforma: $input.plataforma, email: $input.email, updated_at: "now"}
        } as $preferencia_criada
      }
    }

    conditional {
      if ($preferencia_existente != null) {
        db.edit preferencia_aviso {
          field_name = "id"
          field_value = $preferencia_existente.id
          data = {plataforma: $input.plataforma, email: $input.email, updated_at: "now"}
        } as $preferencia_atualizada
      }
    }

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "atualizar_preferencia_aviso"
        recurso      : "preferencia_aviso"
        justificativa: ("assunto=" ~ $input.assunto ~ " plataforma=" ~ ($input.plataforma ? "sim" : "nao") ~ " email=" ~ ($input.email ? "sim" : "nao"))
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    assunto   : $input.assunto
    plataforma: $input.plataforma
    email     : $input.email
  }

  guid = "conectahr-minhas-preferencias-aviso-patch-0001"
}
