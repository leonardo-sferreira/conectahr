// Marca um item do checklist de saida como feito ou pendente (change fluxo-de-desligamento, D1). So
// o RH; so com o desligamento agendado ou concluido; ninguem marca o checklist do proprio desligamento.
// Auditado.
query "solicitacoes_desligamento/{id}/checklist/{item_id}" verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
    int item_id
    bool feito
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

    precondition ($perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH marca o checklist de saida."
    }

    db.get solicitacao_desligamento {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao

    db.get desligamento_checklist {
      field_name = "id"
      field_value = $input.item_id
    } as $item

    precondition (($solicitacao != null) && ($item != null) && ($item.solicitacao_desligamento_id == $solicitacao.id)) {
      error_type = "notfound"
      error = "Item do checklist nao encontrado."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador_alvo

    precondition (($colaborador_alvo == null) || ($colaborador_alvo.user_id != $usuario_autenticado.id)) {
      error_type = "accessdenied"
      error = "Voce nao pode marcar o checklist do proprio desligamento."
    }

    precondition (($solicitacao.status == "agendado") || ($solicitacao.status == "concluido")) {
      error_type = "inputerror"
      error = "O checklist so vale depois de aprovado o desligamento."
    }

    db.edit desligamento_checklist {
      field_name = "id"
      field_value = $item.id
      data = {feito: $input.feito, feito_em: ($input.feito ? "now" : null), feito_por_user_id: ($input.feito ? $usuario_autenticado.id : null), updated_at: "now"}
    } as $item_alterado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "marcar_checklist_desligamento"
        recurso    : "solicitacao_desligamento"
        registro_id: $solicitacao.id
        valor_novo : ($item.titulo ~ ": " ~ ($input.feito ? "feito" : "pendente"))
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Checklist atualizado."
    item    : $item_alterado
  }

  guid = "conectahr-desligamento-checklist-item-post-0001"
}
