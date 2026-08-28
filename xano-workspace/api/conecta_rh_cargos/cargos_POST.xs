// Cadastra um novo cargo.
// Permitido somente para ADMIN e RH.
// Impede nome duplicado e salário negativo.
query cargos verb=POST {
  api_group = "ConectaRH — Cargos"
  auth = "user"

  input {
    text nome filters=trim|min:2|max:100
    text descricao filters=trim|max:500
    decimal salario_base filters=min:0
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
  
    // Impede operações feitas por contas desativadas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Normaliza o perfil do usuário autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem cadastrar cargos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para cadastrar cargos."
    }
  
    // Procura um cargo com o mesmo nome.
    db.get cargo {
      field_name = "nome"
      field_value = $input.nome
    } as $cargo_existente
  
    // Impede nomes duplicados.
    precondition ($cargo_existente == null) {
      error_type = "inputerror"
      error = "Já existe um cargo cadastrado com este nome."
    }
  
    // Cria o cargo.
    db.add cargo {
      data = {
        nome        : $input.nome
        descricao   : $input.descricao
        salario_base: $input.salario_base
        ativo       : $input.ativo
        updated_at  : "now"
      }
    } as $cargo_criado
  }

  response = {
    sucesso : true
    mensagem: "Cargo cadastrado com sucesso."
    cargo   : ```
        {
          id: $cargo_criado.id
          created_at: $cargo_criado.created_at
          updated_at: $cargo_criado.updated_at
          nome: $cargo_criado.nome
          descricao: $cargo_criado.descricao
          salario_base: $cargo_criado.salario_base
          ativo: $cargo_criado.ativo
        }
      ```
  }

  guid = "jLo4b-bRZtzMY5ovj-x5WEfo4TE"
}