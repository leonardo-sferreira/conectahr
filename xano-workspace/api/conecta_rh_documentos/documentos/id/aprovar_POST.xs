// Aprova um documento em analise.
// Operacao permitida somente para RH ou ADMIN.
// Somente documentos pendente_analise podem ser aprovados.
query "documentos/{id}/aprovar" verb=POST {
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

    // Somente RH ou ADMIN podem aprovar documentos.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem aprovar documentos."
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

    // Somente documentos pendentes de analise podem ser aprovados.
    precondition ($documento_atual.status == "pendente_analise") {
      error_type = "inputerror"
      error = "Somente documentos com status pendente_analise podem ser aprovados."
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

    // Aprova o documento.
    db.edit documento {
      field_name = "id"
      field_value = $documento_atual.id
      data = {
        status    : "aprovado"
        observacao: $observacao_final
        updated_at: "now"
      }
    } as $documento_aprovado

    // Auditoria: decisao de aprovacao de documento.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "aprovar_documento"
        recurso       : "documento"
        registro_id   : $documento_atual.id
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Documento aprovado com sucesso."
    documento: $documento_aprovado
  }

  guid = "conectahr-documentos-aprovar-0001"
}
