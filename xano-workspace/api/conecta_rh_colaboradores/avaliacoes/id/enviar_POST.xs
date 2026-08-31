// O avaliador finaliza e envia a avaliacao: calcula a nota geral como
// media das respostas por competencia e marca como enviada. Depois de
// enviada, a avaliacao nao pode ser respondida novamente (decisao
// imutavel em trilha de auditoria).
query "avaliacoes/{id}/enviar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text? comentario? filters=trim|max:2000
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

    db.get avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $avaliacao_atual

    precondition ($avaliacao_atual != null) {
      error_type = "notfound"
      error = "Avaliacao nao encontrada."
    }

    precondition ($avaliacao_atual.user_id == $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Somente o avaliador designado pode enviar esta avaliacao."
    }

    precondition ($avaliacao_atual.status == "pendente" || $avaliacao_atual.status == "em_andamento") {
      error_type = "inputerror"
      error = "Esta avaliacao ja foi enviada ou cancelada."
    }

    db.query resposta_avaliacao {
      where = $db.resposta_avaliacao.avaliacao_id == $avaliacao_atual.id
      return = {type: "list"}
    } as $respostas

    precondition (($respostas|count) > 0) {
      error_type = "inputerror"
      error = "Registre ao menos uma resposta antes de enviar a avaliacao."
    }

    var $soma_notas {
      value = 0
    }

    foreach ($respostas) {
      each as $resposta_item {
        var.update $soma_notas {
          value = $soma_notas + $resposta_item.nota
        }
      }
    }

    var $nota_geral {
      value = $soma_notas / ($respostas|count)
    }

    db.edit avaliacao {
      field_name = "id"
      field_value = $avaliacao_atual.id
      data = {
        status         : "enviada"
        nota           : $nota_geral
        comentario     : $input.comentario
        data_avaliacao : "now"
        updated_at     : "now"
      }
    } as $avaliacao_enviada

    // Auditoria: envio de avaliacao (decisao imutavel).
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "enviar_avaliacao"
        recurso    : "avaliacao"
        registro_id: $avaliacao_atual.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    mensagem  : "Avaliacao enviada com sucesso."
    avaliacao : $avaliacao_enviada
  }

  guid = "conectahr-avaliacoes-enviar-post-0001"
}
