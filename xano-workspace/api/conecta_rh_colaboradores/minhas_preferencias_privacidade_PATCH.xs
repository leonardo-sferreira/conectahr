// Atualiza as preferencias de privacidade do proprio colaborador. Os dois campos
// sao obrigatorios (como em `minhas_preferencias_notificacao`), para um `false`
// explicito nao ser confundido com "nao informado". Auditado, sem dado pessoal.
query minhas_preferencias_privacidade verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    bool ocultar_aniversario
    bool ocultar_mural
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

    conditional {
      if ($preferencia_existente == null) {
        db.add preferencia_privacidade {
          data = {
            colaborador_id     : $colaborador_proprio.id
            ocultar_aniversario: $input.ocultar_aniversario
            ocultar_mural      : $input.ocultar_mural
          }
        } as $preferencia_criada
      }

      else {
        db.edit preferencia_privacidade {
          field_name = "id"
          field_value = $preferencia_existente.id
          data = {
            ocultar_aniversario: $input.ocultar_aniversario
            ocultar_mural      : $input.ocultar_mural
            updated_at         : "now"
          }
        } as $preferencia_atualizada
      }
    }

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "atualizar_preferencia_privacidade"
        recurso      : "preferencia_privacidade"
        justificativa: ("ocultar_aniversario=" ~ ($input.ocultar_aniversario|to_text) ~ "; ocultar_mural=" ~ ($input.ocultar_mural|to_text))
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso            : true
    ocultar_aniversario: $input.ocultar_aniversario
    ocultar_mural      : $input.ocultar_mural
  }

  guid = "conectahr-minhas-preferencias-privacidade-patch-0001"
}
