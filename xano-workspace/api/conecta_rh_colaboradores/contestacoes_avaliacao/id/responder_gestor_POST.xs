// O Gestor que avaliou responde a contestacao (change backend-gestor-pendencias, D5): manter, com justificativa, ou
// revisar, com nova nota de 1 a 5. A nota revisada passa a valer na avaliacao e a original fica em `nota_original`.
// A contestacao continua aberta: o RH tem a palavra final (`revisar`). Uma resposta por contestacao. Auditado.
query "contestacoes_avaliacao/{id}/responder_gestor" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text decisao filters=trim|lower
    decimal? nota?
    text justificativa filters=trim|max:2000
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

    db.get contestacao_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $contestacao

    var $avaliacao_id_c {
      value = ($contestacao != null) ? $contestacao.avaliacao_id : 0
    }

    db.get avaliacao {
      field_name = "id"
      field_value = $avaliacao_id_c
    } as $avaliacao_c

    // Mesma recusa para contestacao inexistente e para quem nao e o avaliador: nao revela se ela existe.
    precondition (($contestacao != null) && ($avaliacao_c != null) && ($avaliacao_c.user_id == $usuario_autenticado.id) && ($avaliacao_c.relacao_avaliador == "gestor")) {
      error_type = "accessdenied"
      error = "Somente o gestor que fez a avaliacao responde esta contestacao."
    }

    precondition ($contestacao.status == "aberta") {
      error_type = "inputerror"
      error = "Esta contestacao ja foi fechada pelo RH."
    }

    precondition ($contestacao.decisao_gestor == null) {
      error_type = "inputerror"
      error = "Voce ja respondeu esta contestacao."
    }

    precondition (($input.decisao == "manter") || ($input.decisao == "revisar")) {
      error_type = "inputerror"
      error = "Decisao invalida. Use manter ou revisar."
    }

    precondition (($input.justificativa|strlen) >= 5) {
      error_type = "inputerror"
      error = "Escreva a justificativa (pelo menos 5 caracteres)."
    }

    precondition (($input.decisao == "manter") || (($input.nota != null) && ($input.nota >= 1) && ($input.nota <= 5))) {
      error_type = "inputerror"
      error = "Para revisar, informe a nova nota, de 1 a 5."
    }

    var $nota_revisada {
      value = ($input.decisao == "revisar") ? $input.nota : null
    }

    db.edit contestacao_avaliacao {
      field_name = "id"
      field_value = $contestacao.id
      data = {
        decisao_gestor               : $input.decisao
        nota_revisada                : $nota_revisada
        resposta_gestor              : $input.justificativa
        respondido_gestor_em         : "now"
        respondido_gestor_por_user_id: $usuario_autenticado.id
        updated_at                   : "now"
      }
    } as $contestacao_respondida

    var $nota_antes {
      value = $avaliacao_c.nota
    }

    conditional {
      if ($input.decisao == "revisar") {
        var $original {
          value = ($avaliacao_c.nota_original != null) ? $avaliacao_c.nota_original : $avaliacao_c.nota
        }

        db.edit avaliacao {
          field_name = "id"
          field_value = $avaliacao_c.id
          data = {
            nota         : $input.nota
            nota_original: $original
            updated_at   : "now"
          }
        } as $avaliacao_revisada
      }
    }

    var $nota_depois {
      value = ($input.decisao == "revisar") ? $input.nota : $avaliacao_c.nota
    }

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "responder_contestacao_gestor"
        recurso       : "contestacao_avaliacao"
        registro_id   : $contestacao.id
        resultado     : "sucesso"
        justificativa : $input.decisao
        valor_anterior: ($nota_antes|to_text)
        valor_novo    : ($nota_depois|to_text)
      }
    } as $evento_auditoria
  }

  response = {
    sucesso     : true
    mensagem    : "Resposta registrada. O RH da a palavra final."
    contestacao : $contestacao_respondida
  }

  guid = "conectahr-contestacoes-avaliacao-responder-gestor-post-0001"
}
