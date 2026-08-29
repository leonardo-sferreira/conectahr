// Consulta um cargo pelo ID.
// Permitido somente para ADMIN e RH.
query "cargos/{id}" verb=GET {
  api_group = "ConectaRH — Cargos"
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil para verificar a permissão.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem consultar cargos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para consultar cargos."
    }
  
    // Localiza o cargo solicitado.
    db.get cargo {
      field_name = "id"
      field_value = $input.id
    } as $cargo
  
    // Retorna erro quando o cargo não existe.
    precondition ($cargo != null) {
      error_type = "notfound"
      error = "Cargo não encontrado."
    }
  }

  response = {sucesso: true, cargo: $cargo}
  guid = "c4F-ngXJj4xOgBUWYK8MwPSRGiE"
}