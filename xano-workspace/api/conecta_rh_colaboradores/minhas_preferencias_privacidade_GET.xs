// Preferencias de privacidade do proprio colaborador (aniversariantes e mural).
// Sem linha gravada, devolve o padrao: oculto para menores de 18 anos, visivel
// para adultos, com `padrao = true`.
query minhas_preferencias_privacidade verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_proprio

    precondition ($colaborador_proprio != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    function.run "ConectaHR/idade_em_anos" {
      input = {data_nascimento: $colaborador_proprio.data_nascimento}
    } as $idade_proprio

    var $menor_de_idade {
      value = ($idade_proprio != null && $idade_proprio < 18)
    }

    db.query preferencia_privacidade {
      where = $db.preferencia_privacidade.colaborador_id == $colaborador_proprio.id
      return = {type: "single"}
    } as $preferencia_existente

    var $aniversario_efetivo {
      value = ($preferencia_existente != null ? $preferencia_existente.ocultar_aniversario : $menor_de_idade)
    }

    var $mural_efetivo {
      value = ($preferencia_existente != null ? $preferencia_existente.ocultar_mural : $menor_de_idade)
    }
  }

  response = {
    sucesso            : true
    ocultar_aniversario: $aniversario_efetivo
    ocultar_mural      : $mural_efetivo
    padrao             : ($preferencia_existente == null)
    menor_de_idade     : $menor_de_idade
  }

  guid = "conectahr-minhas-preferencias-privacidade-get-0001"
}
