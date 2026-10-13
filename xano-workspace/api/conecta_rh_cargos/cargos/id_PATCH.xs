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
    text? senioridade? filters=trim
    int? departamento_id?
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

    // Atualiza somente os dados permitidos (o nivel tem o endpoint proprio, cargos/{id}/nivel).
    db.edit cargo {
      field_name = "id"
      field_value = $cargo_atual.id
      data = {
        nome           : $input.nome
        descricao      : $input.descricao
        salario_base   : $input.salario_base
        senioridade    : $senioridade_final
        departamento_id: $input.departamento_id
        updated_at     : "now"
      }
    } as $cargo_atualizado

    // Auditoria (sem o salario: dado de remuneracao nao vai inteiro para a auditoria).
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "editar_cargo"
        recurso       : "cargo"
        registro_id   : $cargo_atual.id
        valor_anterior: "nome=" ~ $cargo_atual.nome ~ "; senioridade=" ~ ($cargo_atual.senioridade|to_text) ~ "; departamento_id=" ~ ($cargo_atual.departamento_id|to_text)
        valor_novo    : "nome=" ~ $input.nome ~ "; senioridade=" ~ ($senioridade_final|to_text) ~ "; departamento_id=" ~ ($input.departamento_id|to_text)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
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