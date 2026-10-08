// Rejeita um documento em analise.
// Operacao permitida somente para RH ou ADMIN.
// A justificativa da rejeicao e obrigatoria.
// Somente documentos pendente_analise podem ser rejeitados.
query "documentos/{id}/rejeitar" verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int id
    text observacao filters=trim|min:5|max:1000
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
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

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    // Somente RH ou ADMIN podem rejeitar documentos.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem rejeitar documentos."
    }

    // Localiza o documento.
    db.get documento {
      field_name = "id"
      field_value = $input.id
    } as $documento_atual

    precondition ($documento_atual != null) {
      error_type = "notfound"
      error = "Documento nao encontrado."
    }

    // Bloqueio de autoaprovacao: ninguem decide uma solicitacao em que e o
    // proprio colaborador, nem RH/ADMIN. A tentativa e auditada antes da recusa.
    db.get colaborador {
      field_name = "user_id"
      field_value = $auth.id
    } as $colaborador_do_decisor

    conditional {
      if ($colaborador_do_decisor != null && $colaborador_do_decisor.id == $documento_atual.colaborador_id) {
        db.add auditoria {
          data = {
            user_id    : $auth.id
            acao       : "autoaprovacao_bloqueada"
            recurso    : "documento"
            registro_id: $documento_atual.id
            resultado  : "falha"
          }
        } as $evento_autoaprovacao

        precondition (false) {
          error_type = "accessdenied"
          error = "Voce nao pode decidir uma solicitacao propria."
        }
      }
    }

    // Somente documentos pendentes de analise podem ser rejeitados.
    precondition ($documento_atual.status == "pendente_analise") {
      error_type = "inputerror"
      error = "Somente documentos com status pendente_analise podem ser rejeitados."
    }

    // Rejeita o documento e registra a justificativa.
    db.edit documento {
      field_name = "id"
      field_value = $documento_atual.id
      data = {
        status    : "rejeitado"
        observacao: $input.observacao
        updated_at: "now"
      }
    } as $documento_rejeitado

    // Auditoria: decisao de rejeicao de documento.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "rejeitar_documento"
        recurso       : "documento"
        registro_id   : $documento_atual.id
        justificativa : $input.observacao
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Documento rejeitado com sucesso."
    documento: $documento_rejeitado
  }

  guid = "conectahr-documentos-rejeitar-0001"
}
