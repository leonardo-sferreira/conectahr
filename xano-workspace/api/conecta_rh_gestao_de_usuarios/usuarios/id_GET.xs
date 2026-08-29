// Consulta um usuário específico
// Consulta os dados de um usuário sem expor a senha.
query "usuarios/{id}" verb=GET {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
  }

  stack {
    // Identifica quem está realizando a consulta.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil do solicitante.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente ADMIN e RH podem consultar usuários.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Você não possui permissão para consultar usuários."
    }
  
    // Localiza o usuário solicitado.
    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_consultado
  
    precondition ($usuario_consultado != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }
  
    // Normaliza o perfil do usuário consultado.
    var $perfil_consultado {
      value = $usuario_consultado.perfil|trim|to_upper
    }
  
    // RH não pode consultar uma conta ADMIN.
    precondition ($perfil_autenticado == "ADMIN" || $perfil_consultado != "ADMIN") {
      error_type = "accessdenied"
      error = "RH não possui permissão para consultar uma conta ADMIN."
    }
  
    // Procura o colaborador vinculado à conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_consultado.id
    } as $colaborador
  }

  response = {
    usuario: ```
      {
        id: $usuario_consultado.id
        created_at: $usuario_consultado.created_at
        nome: $usuario_consultado.nome
        email: $usuario_consultado.email
        perfil: $perfil_consultado
        ativo: $usuario_consultado.ativo
        ultimo_acesso: $usuario_consultado.ultimo_acesso
        colaborador_id: ($colaborador != null ? $colaborador.id : null)
      }
      ```
  }

  guid = "bxGaG06bVfu9fQzRk_akjkCo5QE"
}