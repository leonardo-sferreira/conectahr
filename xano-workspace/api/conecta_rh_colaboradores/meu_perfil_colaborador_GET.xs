// Retorna o perfil profissional do usuario autenticado.
// Nao recebe colaborador_id ou user_id.
// Retorna nivel e nivel_desde somente para consulta.
// Nao retorna a senha da conta.
query meu_perfil_colaborador verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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
  
    // Localiza o colaborador pelo vinculo da conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
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
    nivel       : $colaborador.nivel
    nivel_desde : $colaborador.nivel_desde
  }

  guid = "sV1L1lUu87he5PMLraux1bcnRRY"
}