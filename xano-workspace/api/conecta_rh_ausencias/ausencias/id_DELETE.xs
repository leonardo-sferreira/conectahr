// Bloqueia a exclusao fisica de registros de ausencia.
// O historico deve ser preservado para consulta e auditoria.
// Nenhum perfil possui permissao para excluir.
query "ausencias/{id}" verb=DELETE {
  api_group = "ConectaRH - Ausencias"
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
  
    // Tokens de contas inativas tambem sao bloqueados.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Localiza o registro apenas para fornecer uma resposta adequada.
    db.get ausencia {
      field_name = "id"
      field_value = $input.id
    } as $ausencia
  
    precondition ($ausencia != null) {
      error_type = "notfound"
      error = "Ausencia nao encontrada."
    }
  
    // Bloqueia permanentemente a exclusao fisica.
    precondition (false) {
      error_type = "accessdenied"
      error = "Registros de ausencia nao podem ser excluidos. O historico deve ser preservado."
    }
  }

  response = {
    sucesso : false
    mensagem: "Exclusao fisica de ausencia bloqueada."
  }

  guid = "ZjOJqbQgZbMQMmhZU_JILHsn0C0"
}