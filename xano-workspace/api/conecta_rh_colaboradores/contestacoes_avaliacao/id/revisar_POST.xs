// RH/ADMIN revisa (resolve) uma contestacao de avaliacao, registrando
// a resposta da revisao. Nao altera a avaliacao original.
query "contestacoes_avaliacao/{id}/revisar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text resposta_revisao filters=trim|min:5|max:2000
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
      error = "Somente RH ou ADMIN podem revisar contestacoes."
    }

    db.get contestacao_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $contestacao_atual

    precondition ($contestacao_atual != null) {
      error_type = "notfound"
      error = "Contestacao nao encontrada."
    }

    // Bloqueio de autoaprovacao: ninguem decide uma solicitacao em que e o
    // proprio colaborador, nem RH/ADMIN. A tentativa e auditada antes da recusa.
    db.get colaborador {
      field_name = "user_id"
      field_value = $auth.id
    } as $colaborador_do_decisor

    conditional {
      if ($colaborador_do_decisor != null && $colaborador_do_decisor.id == $contestacao_atual.colaborador_id) {
        db.add auditoria {
          data = {
            user_id    : $auth.id
            acao       : "autoaprovacao_bloqueada"
            recurso    : "contestacao_avaliacao"
            registro_id: $contestacao_atual.id
            resultado  : "falha"
          }
        } as $evento_autoaprovacao

        precondition (false) {
          error_type = "accessdenied"
          error = "Voce nao pode decidir uma solicitacao propria."
        }
      }
    }

    precondition ($contestacao_atual.status == "aberta") {
      error_type = "inputerror"
      error = "Esta contestacao ja foi revisada."
    }

    db.edit contestacao_avaliacao {
      field_name = "id"
      field_value = $contestacao_atual.id
      data = {
        status              : "revisada"
        revisado_por_user_id  : $usuario_autenticado.id
        resposta_revisao         : $input.resposta_revisao
        data_revisao                : "now"
        updated_at                     : "now"
      }
    } as $contestacao_revisada

    // Auditoria: revisao de contestacao de avaliacao.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "revisar_contestacao_avaliacao"
        recurso       : "contestacao_avaliacao"
        registro_id   : $contestacao_atual.id
        justificativa : $input.resposta_revisao
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Contestacao revisada com sucesso."
    contestacao : $contestacao_revisada
  }

  guid = "conectahr-contestacoes-avaliacao-revisar-post-0001"
}
