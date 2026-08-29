// Ativa ou inativa um cargo sem excluir o registro.
// Permitido somente para ADMIN e RH.
// A alteração não remove vínculos existentes com colaboradores.
query "cargos/{id}/status" verb=PATCH {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
    int id
    bool ativo
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
  
    // Impede operações realizadas por contas desativadas.
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
  
    // Somente ADMIN e RH podem alterar o status de cargos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para alterar o status de cargos."
    }
  
    // Localiza o cargo selecionado.
    db.get cargo {
      field_name = "id"
      field_value = $input.id
    } as $cargo_atual
  
    precondition ($cargo_atual != null) {
      error_type = "notfound"
      error = "Cargo não encontrado."
    }
  
    // Altera somente o status e a data de atualização.
    db.edit cargo {
      field_name = "id"
      field_value = $cargo_atual.id
      data = {ativo: $input.ativo, updated_at: "now"}
    } as $cargo_atualizado
  }

  response = {
    sucesso : true
    mensagem: ($cargo_atualizado.ativo == true ? "Cargo ativado com sucesso." : "Cargo inativado com sucesso.")
    cargo   : ```
        {
          id: $cargo_atualizado.id
          nome: $cargo_atualizado.nome
          descricao: $cargo_atualizado.descricao
          salario_base: $cargo_atualizado.salario_base
          ativo: $cargo_atualizado.ativo
          updated_at: $cargo_atualizado.updated_at
        }
      ```
  }

  guid = "qqsxsD5s4f1pAr23qWeMaWlvn68"
}