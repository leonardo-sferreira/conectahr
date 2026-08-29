// Cadastra um novo departamento.
// Permitido somente para ADMIN e RH.
// Impede o cadastro de nomes duplicados.
query departamentos verb=POST {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
    text nome filters=trim|min:2|max:100
    text descricao filters=trim|max:500
    bool ativo
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
  
    // Impede operações feitas por contas desativadas.
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
  
    // Somente ADMIN e RH podem cadastrar departamentos.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para cadastrar departamentos."
    }
  
    // Procura um departamento com o mesmo nome.
    db.get departamento {
      field_name = "nome"
      field_value = $input.nome
    } as $departamento_existente
  
    // Impede o cadastro duplicado.
    precondition ($departamento_existente == null) {
      error_type = "inputerror"
      error = "Já existe um departamento cadastrado com este nome."
    }
  
    // Cria o departamento.
    db.add departamento {
      data = {
        nome      : $input.nome
        descricao : $input.descricao
        ativo     : $input.ativo
        updated_at: "now"
      }
    } as $departamento_criado
  }

  response = {
    sucesso     : true
    mensagem    : "Departamento cadastrado com sucesso."
    departamento: ```
        {
          id: $departamento_criado.id
          created_at: $departamento_criado.created_at
          updated_at: $departamento_criado.updated_at
          nome: $departamento_criado.nome
          descricao: $departamento_criado.descricao
          ativo: $departamento_criado.ativo
        }
      ```
  }

  guid = "yR3IThzu9Ty9WbqgV_WsJS7olbQ"
}