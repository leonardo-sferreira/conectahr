// Autenticação de usuário do ConectaRH
// Autentica um usuário ativo e retorna o token e a situação do primeiro acesso.
query "auth/login" verb=POST {
  api_group = "ConectaRH — Autenticação"

  input {
    email email filters=trim|lower
    text password
  }

  stack {
    // Carrega o usuário completo, incluindo a senha protegida.
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $user
  
    // Não revela se o e-mail existe.
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "E-mail ou senha inválidos."
    }
  
    // Bloqueia contas desativadas.
    precondition ($user.ativo) {
      error_type = "accessdenied"
      error = "E-mail ou senha inválidos."
    }
  
    // Compara a senha informada com o hash armazenado.
    security.check_password {
      text_password = $input.password
      hash_password = $user.senha
    } as $pass_result
  
    precondition ($pass_result) {
      error_type = "accessdenied"
      error = "E-mail ou senha inválidos."
    }
  
    // Procura o colaborador vinculado à conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $user.id
    } as $colaborador
  
    // Atualiza o último acesso.
    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {ultimo_acesso: "now"}
    } as $user_atualizado
  
    // Gera um token válido por uma hora.
    security.create_auth_token {
      table = "user"
      extras = {perfil: $user.perfil}
      expiration = 3600
      id = $user.id
    } as $auth_token
  }

  response = {
    token                : $auth_token
    tipo                 : "Bearer"
    expira_em_segundos   : 3600
    senha_primeiro_acesso: $user.senha_primeiro_acesso
    usuario              : ```
      {
        id: $user.id
        nome: $user.nome
        email: $user.email
        perfil: $user.perfil
        ativo: $user.ativo
        colaborador_id: ($colaborador != null ? $colaborador.id : null)
      }
      ```
  }

  guid = "ODyvwjfBqn40N51ETK1huleI1CM"
}