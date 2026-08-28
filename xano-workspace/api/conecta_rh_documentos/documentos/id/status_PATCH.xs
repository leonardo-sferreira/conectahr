// Altera o status logico de um documento.
// Somente RH ou ADMIN podem arquivar ou reativar.
// O documento nao e excluido fisicamente.
query "documentos/{id}/status" verb=PATCH {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int id
    bool ativo
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
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem alterar o status.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem alterar o status de documentos."
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
  
    // Confirma que o colaborador proprietario ainda existe.
    db.get colaborador {
      field_name = "id"
      field_value = $documento_atual.colaborador_id
    } as $colaborador_proprietario
  
    precondition ($colaborador_proprietario != null) {
      error_type = "notfound"
      error = "Colaborador proprietario do documento nao encontrado."
    }
  
    // Altera somente ativo e updated_at.
    db.edit documento {
      field_name = "id"
      field_value = $documento_atual.id
      data = {ativo: $input.ativo, updated_at: "now"}
    } as $documento_atualizado
  }

  response = {
    sucesso  : true
    mensagem : "Status do documento alterado com sucesso."
    documento: $documento_atualizado
  }

  guid = "l2o_sVoRRPe_gXqT8_GKziegrO8"
}