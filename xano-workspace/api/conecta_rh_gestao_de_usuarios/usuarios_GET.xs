// Lista os usuários cadastrados no ConectaRH
// Lista usuários para os perfis ADMIN e RH sem expor senhas.
query usuarios verb=GET {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
  }

  stack {
    // Identifica o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    // Confirma que o usuário existe.
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Bloqueia contas desativadas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Remove espaços e converte o perfil para maiúsculas.
    var $perfil_normalizado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Permite acesso somente para ADMIN ou RH.
    precondition ($perfil_normalizado == "ADMIN" || $perfil_normalizado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para consultar usuários."
    }
  
    // Lista os usuários sem retornar a coluna senha.
    db.query user {
      return = {type: "list"}
      output = [
        "id"
        "created_at"
        "nome"
        "email"
        "perfil"
        "ativo"
        "ultimo_acesso"
      ]
    } as $usuarios
  }

  response = {
    perfil_autenticado: $perfil_normalizado
    usuarios          : $usuarios
  }

  guid = "cnMROPTlSsq-_R-Lj_htESZQVwQ"
}