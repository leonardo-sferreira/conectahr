// Ativa ou desativa uma conta de usuário sem excluir seu histórico.
// ADMIN administra contas em geral.
// RH administra somente contas de COLABORADOR.
query "usuarios/{id}/status" verb=PATCH {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    bool ativo
  }

  stack {
    // Localiza o usuário que está realizando a operação.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Uma conta inativa não pode administrar outras contas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Normaliza o perfil do usuário autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem alterar o status de contas.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para alterar o status de usuários."
    }
  
    // Localiza a conta que terá o status alterado.
    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_alvo
  
    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }
  
    // Normaliza o perfil da conta selecionada.
    var $perfil_alvo {
      value = $usuario_alvo.perfil|trim|to_upper
    }
  
    // O RH pode alterar somente contas de colaboradores.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_alvo == "COLABORADOR") {
      error_type = "accessdenied"
      error = "O RH pode alterar somente contas de colaboradores."
    }
  
    // Impede que o usuário desative a própria conta.
    precondition ($input.ativo || $usuario_alvo.id != $usuario_autenticado.id) {
      error_type = "inputerror"
      error = "Você não pode desativar a própria conta."
    }
  
    // Altera somente o campo ativo.
    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {ativo: $input.ativo}
    } as $usuario_atualizado
  }

  response = {
    sucesso : true
    mensagem: ($usuario_atualizado.ativo == true ? "Conta ativada com sucesso." : "Conta desativada com sucesso.")
    usuario : ```
        {
          id: $usuario_atualizado.id
          nome: $usuario_atualizado.nome
          email: $usuario_atualizado.email
          perfil: $usuario_atualizado.perfil
          ativo: $usuario_atualizado.ativo
        }
      ```
  }

  guid = "ASydeqSNSSgWRRM-oqQ6wGjEZQM"
}