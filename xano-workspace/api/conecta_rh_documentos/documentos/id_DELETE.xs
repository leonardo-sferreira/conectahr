// Bloqueia a exclusao fisica de documentos.
// Documentos devem ser arquivados pelo campo ativo.
// Nenhum perfil possui permissao para excluir registros.
query "documentos/{id}" verb=DELETE {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int id
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
  
    // Localiza o documento para diferenciar registro inexistente.
    db.get documento {
      field_name = "id"
      field_value = $input.id
    } as $documento
  
    precondition ($documento != null) {
      error_type = "notfound"
      error = "Documento nao encontrado."
    }
  
    // Bloqueia permanentemente a exclusao.
    precondition (false) {
      error_type = "accessdenied"
      error = "Documentos nao podem ser excluidos. Utilize a alteracao de status para arquivar o registro."
    }
  }

  response = {
    sucesso : false
    mensagem: "Exclusao fisica de documento bloqueada."
  }

  guid = "B5xogTMCxtBYsvmhn6ynxbrVRZU"
}