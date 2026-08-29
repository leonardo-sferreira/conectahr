// Lista os cargos cadastrados no sistema.
// Permitido somente para ADMIN e RH.
query listar_cargos verb=GET {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil para evitar problemas com maiúsculas e espaços.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem consultar os cargos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para consultar cargos."
    }
  
    // Lista todos os cargos em ordem alfabética.
    db.query cargo {
      return = {type: "list"}
    } as $cargos
  }

  response = {sucesso: true, cargos: $cargos}
  guid = "JB5XCpuepK6pWiaxlWFcLN59EZc"
}