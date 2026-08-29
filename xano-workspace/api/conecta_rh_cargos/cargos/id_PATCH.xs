// Atualiza os dados de um cargo existente.
// Não altera o campo ativo.
// Permitido somente para ADMIN e RH.
query "cargos/{id}" verb=PATCH {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    text descricao filters=trim|max:500
    decimal salario_base filters=min:0
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
  
    // Somente ADMIN e RH podem atualizar cargos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para atualizar cargos."
    }
  
    // Localiza o cargo que será atualizado.
    db.get cargo {
      field_name = "id"
      field_value = $input.id
    } as $cargo_atual
  
    precondition ($cargo_atual != null) {
      error_type = "notfound"
      error = "Cargo não encontrado."
    }
  
    // Verifica se o nome já está sendo usado.
    db.get cargo {
      field_name = "nome"
      field_value = $input.nome
    } as $cargo_mesmo_nome
  
    // Aceita o nome quando ele não existe ou pertence ao próprio cargo.
    precondition ($cargo_mesmo_nome == null || $cargo_mesmo_nome.id == $cargo_atual.id) {
      error_type = "inputerror"
      error = "Já existe outro cargo cadastrado com este nome."
    }
  
    // Atualiza somente os dados permitidos.
    db.edit cargo {
      field_name = "id"
      field_value = $cargo_atual.id
      data = {
        nome        : $input.nome
        descricao   : $input.descricao
        salario_base: $input.salario_base
        updated_at  : "now"
      }
    } as $cargo_atualizado
  }

  response = {
    sucesso : true
    mensagem: "Cargo atualizado com sucesso."
    cargo   : ```
        {
          id: $cargo_atualizado.id
          created_at: $cargo_atualizado.created_at
          updated_at: $cargo_atualizado.updated_at
          nome: $cargo_atualizado.nome
          descricao: $cargo_atualizado.descricao
          salario_base: $cargo_atualizado.salario_base
          ativo: $cargo_atualizado.ativo
        }
      ```
  }

  guid = "2Q2y53VeJfofGJbTbfVoHNffNCs"
}