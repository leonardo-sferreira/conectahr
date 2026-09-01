// Arquiva um documento rejeitado, vencido ou substituido.
// Operacao permitida somente para RH ou ADMIN.
// O documento nao e excluido, apenas deixa de ser editavel.
query "documentos/{id}/arquivar" verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int id
    text? observacao? filters=trim|max:1000
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

    // Somente RH ou ADMIN podem arquivar documentos.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem arquivar documentos."
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

    // Somente documentos rejeitados, vencidos ou substituidos podem ser arquivados.
    precondition ($documento_atual.status == "rejeitado" || $documento_atual.status == "vencido" || $documento_atual.status == "substituido") {
      error_type = "inputerror"
      error = "Somente documentos rejeitados, vencidos ou substituidos podem ser arquivados."
    }

    // Preserva a observacao existente por padrao.
    var $observacao_final {
      value = $documento_atual.observacao
    }

    // Substitui a observacao somente quando uma nova for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }

    // Arquiva o documento e encerra sua edicao.
    db.edit documento {
      field_name = "id"
      field_value = $documento_atual.id
      data = {
        status    : "arquivado"
        observacao: $observacao_final
        ativo     : false
        updated_at: "now"
      }
    } as $documento_arquivado

    // Auditoria: arquivamento de documento (item 7.11).
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "arquivar_documento"
        recurso       : "documento"
        registro_id   : $documento_atual.id
        valor_anterior: $documento_atual.status
        valor_novo    : "arquivado"
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Documento arquivado com sucesso."
    documento: $documento_arquivado
  }

  guid = "conectahr-documentos-arquivar-0001"
}
