// Atualiza os dados básicos de uma conta de usuário.
// Não altera senha, perfil, status ativo ou vínculo com colaborador.
query "usuarios/{id}" verb=PATCH {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    email email filters=trim|lower
  }

  stack {
    // Localiza o usuário que está fazendo a alteração.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Impede o uso por contas desativadas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Normaliza o perfil de quem está realizando a operação.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem administrar usuários.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para alterar usuários."
    }
  
    // Localiza a conta que será alterada.
    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_alvo
  
    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }
  
    // Normaliza o perfil da conta que será alterada.
    var $perfil_alvo {
      value = $usuario_alvo.perfil|trim|to_upper
    }
  
    // O RH pode editar somente contas de colaboradores.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_alvo == "COLABORADOR") {
      error_type = "accessdenied"
      error = "O RH pode alterar somente contas de colaboradores."
    }
  
    // Verifica se o novo e-mail já pertence a outra conta.
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $usuario_email_existente
  
    precondition ($usuario_email_existente == null || $usuario_email_existente.id == $usuario_alvo.id) {
      error_type = "inputerror"
      error = "Este e-mail já está vinculado a outra conta."
    }
  
    // Atualiza somente os dados permitidos.
    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {nome: $input.nome, email: $input.email}
    } as $usuario_atualizado
  
    // Localiza o colaborador vinculado à conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_atualizado.id
    } as $colaborador
  }

  response = {
    sucesso : true
    mensagem: "Usuário atualizado com sucesso."
    usuario : ```
        {
          id: $usuario_atualizado.id
          nome: $usuario_atualizado.nome
          email: $usuario_atualizado.email
          perfil: $usuario_atualizado.perfil
          ativo: $usuario_atualizado.ativo
          senha_primeiro_acesso: $usuario_atualizado.senha_primeiro_acesso
          colaborador_id: ($colaborador != null ? $colaborador.id : null)
        }
      ```
  }

  guid = "q65ipgx5I1IosmXvSNu4SUltcfA"
}