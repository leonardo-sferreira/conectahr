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
