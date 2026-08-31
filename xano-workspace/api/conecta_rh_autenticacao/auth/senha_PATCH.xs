// Alteração de senha do usuário autenticado
// Permite ao usuário autenticado alterar a própria senha e concluir o primeiro acesso.
query "auth/senha" verb=PATCH {
  api_group = "ConectaRH — Autenticação"
  auth = "user"

  input {
    text senha_atual
    text nova_senha filters=min:8|max:64
    text confirmar_senha filters=min:8|max:64
  }

  stack {
    // Localiza o usuário identificado pelo token.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $user
  
    // Confirma que o usuário existe.
    precondition ($user != null) {
      error_type = "unauthorized"
      error = "Usuário não encontrado."
    }
  
    // Bloqueia contas desativadas.
    precondition ($user.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Confere a confirmação da nova senha.
    precondition ($input.nova_senha == $input.confirmar_senha) {
      error_type = "inputerror"
      error = "A confirmação não corresponde à nova senha."
    }
  
    // Valida a senha atual.
    security.check_password {
      text_password = $input.senha_atual
      hash_password = $user.senha
    } as $senha_atual_valida
  
    precondition ($senha_atual_valida) {
      error_type = "accessdenied"
      error = "A senha atual está incorreta."
    }
  
    // Impede reutilizar a senha atual.
    security.check_password {
      text_password = $input.nova_senha
      hash_password = $user.senha
    } as $nova_senha_igual
  
    precondition ($nova_senha_igual == false) {
      error_type = "inputerror"
      error = "A nova senha deve ser diferente da senha atual."
    }
  
    // Grava a nova senha e conclui o primeiro acesso.
    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {senha: $input.nova_senha, senha_primeiro_acesso: false}
    } as $user_atualizado

    // Auditoria: troca de senha (nunca a senha em si).
    db.add auditoria {
      data = {
        user_id    : $user.id
        acao       : "troca_senha"
        recurso    : "user"
        registro_id: $user.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso              : true
    mensagem             : "Senha alterada com sucesso. Primeiro acesso concluído."
    usuario_id           : $user_atualizado.id
    senha_primeiro_acesso: $user_atualizado.senha_primeiro_acesso
  }

  guid = "vxc3gNMdyGzZWWdfzr3trm3Vq0s"
}