// Atualiza os dados de um departamento.
// Não altera o campo ativo.
// Permitido somente para ADMIN e RH.
query "departamentos/{id}" verb=PATCH {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    text descricao filters=trim|max:500
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
  
    // Somente ADMIN e RH podem atualizar departamentos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para atualizar departamentos."
    }
  
    // Localiza o departamento que será atualizado.
    db.get departamento {
      field_name = "id"
      field_value = $input.id
    } as $departamento_atual
  
    precondition ($departamento_atual != null) {
      error_type = "notfound"
      error = "Departamento não encontrado."
    }
  
    // Procura outro departamento com o nome informado.
    db.get departamento {
      field_name = "nome"
      field_value = $input.nome
    } as $departamento_mesmo_nome
  
    // Aceita o nome quando não existe ou pertence ao próprio departamento.
    precondition ($departamento_mesmo_nome == null || $departamento_mesmo_nome.id == $departamento_atual.id) {
      error_type = "inputerror"
      error = "Já existe outro departamento cadastrado com este nome."
    }
  
    // Atualiza somente os dados permitidos.
    db.edit departamento {
      field_name = "id"
      field_value = $departamento_atual.id
      data = {
        nome      : $input.nome
        descricao : $input.descricao
        updated_at: "now"
      }
    } as $departamento_atualizado
  }

  response = {
    sucesso     : true
    mensagem    : "Departamento atualizado com sucesso."
    departamento: ```
        {
          id: $departamento_atualizado.id
          created_at: $departamento_atualizado.created_at
          updated_at: $departamento_atualizado.updated_at
          nome: $departamento_atualizado.nome
          descricao: $departamento_atualizado.descricao
          ativo: $departamento_atualizado.ativo
        }
      ```
  }

  guid = "aJx5KhT6JzAaBElcnR9sJv7TFFA"
}