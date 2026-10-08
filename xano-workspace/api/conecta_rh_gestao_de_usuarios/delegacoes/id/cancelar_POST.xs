// Cancela uma delegacao antes do fim da vigencia. O titular ou RH/ADMIN
// podem cancelar.
query "delegacoes/{id}/cancelar" verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get delegacao_aprovacao {
      field_name = "id"
      field_value = $input.id
    } as $delegacao_atual

    precondition ($delegacao_atual != null) {
      error_type = "notfound"
      error = "Delegacao nao encontrada."
    }

    // Autorizacao checada antes do estado de cancelamento, para nao revelar
    // esse estado a quem nao tem permissao sobre a delegacao.
    precondition ($delegacao_atual.titular_user_id == $usuario_autenticado.id || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente o titular, RH ou ADMIN podem cancelar esta delegacao."
    }

    precondition ($delegacao_atual.cancelada_em == null) {
      error_type = "inputerror"
      error = "Esta delegacao ja esta cancelada."
    }

    db.edit delegacao_aprovacao {
      field_name = "id"
      field_value = $delegacao_atual.id
      data = {
        cancelada_em         : "now"
        cancelada_por_user_id  : $usuario_autenticado.id
        updated_at               : "now"
      }
    } as $delegacao_cancelada

    // Auditoria: cancelamento de delegacao.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "cancelar_delegacao_aprovacao"
        recurso    : "delegacao_aprovacao"
        registro_id: $delegacao_atual.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    mensagem  : "Delegacao cancelada com sucesso."
    delegacao : $delegacao_cancelada
  }

  guid = "conectahr-delegacoes-cancelar-post-0001"
}
