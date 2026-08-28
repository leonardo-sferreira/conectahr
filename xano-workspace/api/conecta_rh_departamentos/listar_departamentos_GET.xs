// Lista os departamentos cadastrados no sistema.
// Permitido somente para ADMIN e RH.
query listar_departamentos verb=GET {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuário identificado pelo token.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
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
  
    // Lista os departamentos em ordem alfabética.
    db.query departamento {
      return = {type: "list"}
    } as $departamentos
  }

  response = {sucesso: true, departamentos: $departamentos}
  guid = "ZwGmzT4PmxduehByi9HygcLG3KI"
}