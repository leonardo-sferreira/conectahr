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

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
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
  }

  response = {
    sucesso  : true
    mensagem : "Documento rejeitado com sucesso."
    documento: $documento_rejeitado
  }

  guid = "conectahr-documentos-rejeitar-0001"
}
