// RH/ADMIN modera um reconhecimento publico que nao seja exclusivamente
// positivo (Requirement: "Desenvolvimento e reconhecimento" - conteudo
// corretivo nao pode ficar publico). Marca como `moderado`, com motivo
// auditado; nao apaga o registro.
query "reconhecimentos/{id}/moderar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text motivo_moderacao filters=trim|min:5|max:1000
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem moderar reconhecimentos."
    }

    db.get reconhecimento {
      field_name = "id"
      field_value = $input.id
    } as $reconhecimento_atual

    precondition ($reconhecimento_atual != null) {
      error_type = "notfound"
      error = "Reconhecimento nao encontrado."
    }

    precondition ($reconhecimento_atual.status == "ativo") {
      error_type = "inputerror"
      error = "Somente reconhecimentos ativos podem ser moderados."
    }

    db.edit reconhecimento {
      field_name = "id"
      field_value = $reconhecimento_atual.id
      data = {
        status            : "moderado"
        moderado_por_user_id: $usuario_autenticado.id
        motivo_moderacao     : $input.motivo_moderacao
        updated_at              : "now"
      }
    } as $reconhecimento_moderado

    // Auditoria: moderacao de reconhecimento publico.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "moderar_reconhecimento"
        recurso       : "reconhecimento"
        registro_id   : $reconhecimento_atual.id
        justificativa : $input.motivo_moderacao
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso        : true
    mensagem       : "Reconhecimento moderado."
    reconhecimento : $reconhecimento_moderado
  }

  guid = "conectahr-reconhecimentos-moderar-post-0001"
}
