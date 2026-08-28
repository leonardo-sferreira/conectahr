// Consulta um departamento pelo ID.
// Permitido somente para ADMIN e RH.
query "departamentos/{id}" verb=GET {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuário identificado pelo token.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    // Confirma que o usuário autenticado existe.
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Impede o acesso de contas desativadas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Normaliza o perfil para verificar a permissão.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem consultar departamentos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para consultar departamentos."
    }
  
    // Localiza o departamento solicitado.
    db.get departamento {
      field_name = "id"
      field_value = $input.id
    } as $departamento
  
    // Retorna erro quando o departamento não existe.
    precondition ($departamento != null) {
      error_type = "notfound"
      error = "Departamento não encontrado."
    }
  }

  response = {
    sucesso     : true
    departamento: ```
        {
          id: $departamento.id
          created_at: $departamento.created_at
          updated_at: $departamento.updated_at
          nome: $departamento.nome
          descricao: $departamento.descricao
          ativo: $departamento.ativo
        }
      ```
  }

  guid = "qfXblCEJ4AJ9EP9I9MrrC4NXoEo"
}