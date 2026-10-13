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
    text? senioridade? filters=trim
    int? departamento_id?
    int? nivel_hierarquico_id?
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

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
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
  

    // Senioridade, departamento e nivel (change cadastro-de-cargos, D1, D3 e D4): opcionais e validados.
    precondition ($input.senioridade == null || $input.senioridade == "" || $input.senioridade == "junior" || $input.senioridade == "pleno" || $input.senioridade == "senior" || $input.senioridade == "especialista") {
      error_type = "inputerror"
      error = "Senioridade invalida. Use junior, pleno, senior ou especialista."
    }

    var $senioridade_final {
      value = ($input.senioridade == "" ? null : $input.senioridade)
    }

    conditional {
      if ($input.departamento_id != null) {
        db.get departamento {
          field_name = "id"
          field_value = $input.departamento_id
        } as $departamento_escolhido

        precondition ($departamento_escolhido != null && $departamento_escolhido.ativo) {
          error_type = "inputerror"
          error = "Escolha um departamento ativo."
        }
      }
    }

    conditional {
      if ($input.nivel_hierarquico_id != null) {
        db.get nivel_hierarquico {
          field_name = "id"
          field_value = $input.nivel_hierarquico_id
        } as $nivel_escolhido

        precondition ($nivel_escolhido != null && $nivel_escolhido.ativo) {
          error_type = "inputerror"
          error = "Escolha um nivel ativo."
        }
      }
    }

    // Cria o cargo.
    db.add cargo {
      data = {
        nome                : $input.nome
        descricao           : $input.descricao
        salario_base        : $input.salario_base
        ativo               : $input.ativo
        senioridade         : $senioridade_final
        departamento_id     : $input.departamento_id
        nivel_hierarquico_id: $input.nivel_hierarquico_id
        updated_at          : "now"
      }
    } as $cargo_criado

    // Auditoria (sem o salario: dado de remuneracao nao vai inteiro para a auditoria).
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_cargo"
        recurso    : "cargo"
        registro_id: $cargo_criado.id
        valor_novo : "nome=" ~ $input.nome ~ "; senioridade=" ~ ($senioridade_final|to_text) ~ "; departamento_id=" ~ ($input.departamento_id|to_text) ~ "; nivel_hierarquico_id=" ~ ($input.nivel_hierarquico_id|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
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