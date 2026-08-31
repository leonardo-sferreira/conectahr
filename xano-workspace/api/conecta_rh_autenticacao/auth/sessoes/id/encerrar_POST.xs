// Encerra uma sessao especifica do usuario autenticado, sem afetar as
// demais (Requirement: Sessoes e dispositivos - "Encerramento de
// dispositivo"). Um usuario so pode encerrar as proprias sessoes.
query "auth/sessoes/{id}/encerrar" verb=POST {
  api_group = "ConectaRH — Autenticação"
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

    db.get sessao {
      field_name = "id"
      field_value = $input.id
    } as $sessao_alvo

    precondition ($sessao_alvo != null) {
      error_type = "notfound"
      error = "Sessao nao encontrada."
    }

    precondition ($sessao_alvo.user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce so pode encerrar as proprias sessoes."
    }

    precondition ($sessao_alvo.ativa) {
      error_type = "inputerror"
      error = "Esta sessao ja esta encerrada."
    }

    db.edit sessao {
      field_name = "id"
      field_value = $sessao_alvo.id
      data = {ativa: false, revogada_em: "now", updated_at: "now"}
    } as $sessao_encerrada

    // Auditoria: encerramento de sessao especifica.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "encerrar_sessao"
        recurso    : "sessao"
        registro_id: $sessao_alvo.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Sessao encerrada com sucesso."
    sessao  : $sessao_encerrada
  }

  guid = "conectahr-auth-sessoes-encerrar-post-0001"
}
