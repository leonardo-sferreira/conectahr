// Altera o perfil de acesso de uma conta.
// Operação exclusiva de ADMIN.
// Não altera senha, nome, e-mail, status ou vínculo com colaborador.
query "usuarios/{id}/perfil" verb=PATCH {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    text perfil filters=trim
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Impede o uso por uma conta inativa.
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
  
    // Somente ADMIN pode alterar perfis.
    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente ADMIN pode alterar o perfil de usuários."
    }
  
    // Localiza a conta que terá o perfil alterado.
    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_alvo
  
    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }
  
    // Normaliza o perfil recebido.
    var $perfil_novo {
      value = $input.perfil|trim|to_upper
    }
  
    // Aceita somente os quatro perfis do ConectaRH.
    precondition ($perfil_novo == "ADMIN" || $perfil_novo == "RH" || $perfil_novo == "COLABORADOR" || $perfil_novo == "GESTOR") {
      error_type = "inputerror"
      error = "Perfil inválido. Use ADMIN, RH, COLABORADOR ou GESTOR."
    }
  
    // Impede que o ADMIN altere o próprio perfil.
    precondition ($usuario_alvo.id != $usuario_autenticado.id) {
      error_type = "inputerror"
      error = "Você não pode alterar o próprio perfil."
    }
  
    // Converte para os valores exatos configurados no Enum:
    // Admin, RH, Colaborador e Gestor.
    var $perfil_valor_banco {
      value = ```
          (
            $perfil_novo == "ADMIN"
            ? "Admin"
            : (
              $perfil_novo == "RH"
              ? "RH"
              : (
                $perfil_novo == "GESTOR"
                ? "Gestor"
                : "Colaborador"
              )
            )
          )
        ```
    }
  
    // Altera somente o perfil.
    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {perfil: $perfil_valor_banco}
    } as $usuario_atualizado
  
    // Normaliza o perfil apenas para a resposta.
    var $perfil_resposta {
      value = $usuario_atualizado.perfil|trim|to_upper
    }
  }

  response = {
    sucesso : true
    mensagem: "Perfil do usuário alterado com sucesso."
    usuario : ```
        {
          id: $usuario_atualizado.id
          nome: $usuario_atualizado.nome
          email: $usuario_atualizado.email
          perfil: $perfil_resposta
          ativo: $usuario_atualizado.ativo
        }
      ```
  }

  guid = "35VZpHvNmpUJA0XzwgAmAafXxlA"
}