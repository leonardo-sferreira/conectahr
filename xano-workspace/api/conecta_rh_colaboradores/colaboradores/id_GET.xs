// Consulta um colaborador especifico pelo ID.
// Permitido somente para RH e ADMIN.
// Retorna o registro completo, incluindo nivel e nivel_desde.
// Nao consulta nem retorna a senha da tabela user.
query "colaboradores/{id}" verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem consultar qualquer colaborador.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para consultar colaboradores."
    }
  
    // Localiza o colaborador.
    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }
  
    // Localiza o cargo vinculado.
    db.get cargo {
      field_name = "id"
      field_value = $colaborador.cargo_id
    } as $cargo
  
    // Localiza o departamento vinculado.
    db.get departamento {
      field_name = "id"
      field_value = $colaborador.departamento_id
    } as $departamento
  }

  response = {
    sucesso     : true
    colaborador : $colaborador
    cargo       : $cargo
    departamento: $departamento
  }

  guid = "B1wTEU1G-jI3GsP8C3z4v9WKtfc"
}