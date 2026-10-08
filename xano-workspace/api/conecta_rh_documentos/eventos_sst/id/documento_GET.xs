// Abre o documento de um evento de SST (ASO e similares) e registra o acesso na
// auditoria (acessar_arquivo_documento). Mesmo escopo da consulta de eventos:
// RH/ADMIN ou o proprio colaborador; o Gestor NAO tem acesso.
query "eventos_sst/{id}/documento" verb=GET {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int id
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

    db.get evento_sst {
      field_name = "id"
      field_value = $input.id
    } as $evento

    precondition ($evento != null) {
      error_type = "notfound"
      error = "Evento de SST nao encontrado."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $evento.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo.user_id == $usuario_autenticado.id)
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para abrir este documento de SST."
    }

    var $tem_documento {
      value = (($evento.documento_url != null) && (($evento.documento_url|trim) != ""))
    }

    precondition ($tem_documento) {
      error_type = "notfound"
      error = "Este evento nao possui documento."
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "acessar_arquivo_documento"
        recurso    : "evento_sst"
        registro_id: $evento.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria_acesso
  }

  response = {
    sucesso     : true
    evento_id   : $evento.id
    documento_url: ($evento.documento_url|trim)
  }

  guid = "conectahr-eventos-sst-documento-get-0001"
}
