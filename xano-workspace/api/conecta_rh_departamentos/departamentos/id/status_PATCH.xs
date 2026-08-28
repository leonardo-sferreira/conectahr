// Ativa ou inativa um departamento sem excluir o registro.
// Permitido somente para ADMIN e RH.
// Não remove os vínculos existentes com colaboradores.
query "departamentos/{id}/status" verb=PATCH {
  api_group = "ConectaRH — Departamentos"
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
  
    // Normaliza o perfil para verificar a permissão.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem alterar o status de departamentos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para alterar o status de departamentos."
    }
  
    // Localiza o departamento selecionado.
    db.get departamento {
      field_name = "id"
      field_value = $input.id
    } as $departamento_atual
  
    precondition ($departamento_atual != null) {
      error_type = "notfound"
      error = "Departamento não encontrado."
    }
  
    // Altera somente o status e a data de atualização.
    db.edit departamento {
      field_name = "id"
      field_value = $departamento_atual.id
      data = {ativo: $input.ativo, updated_at: "now"}
    } as $departamento_atualizado
  }

  response = {
    sucesso     : true
    mensagem    : ($departamento_atualizado.ativo == true ? "Departamento ativado com sucesso." : "Departamento inativado com sucesso.")
    departamento: ```
        {
          id: $departamento_atualizado.id
          nome: $departamento_atualizado.nome
          descricao: $departamento_atualizado.descricao
          ativo: $departamento_atualizado.ativo
          updated_at: $departamento_atualizado.updated_at
        }
      ```
  }

  guid = "1X-co3gaUKV_5nombYKVoqhBr5Y"
}