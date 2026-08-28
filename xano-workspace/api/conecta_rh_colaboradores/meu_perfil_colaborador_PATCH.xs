// Permite ao usuário autenticado atualizar seus próprios dados
// de contato, endereço e e-mail pessoal.
// Não recebe ID e não altera dados profissionais,
// permissões ou o e-mail de login.
query meu_perfil_colaborador verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text email_pessoal filters=trim|max:255
    text telefone filters=trim|max:20
    text cep filters=trim|max:9
    text logradouro filters=trim|max:150
    text numero filters=trim|max:20
    text complemento filters=trim|max:100
    text bairro filters=trim|max:100
    text cidade filters=trim|max:100
    text estado filters=trim|min:2|max:2
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
  
    // Uma conta inativa não pode atualizar o perfil.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Localiza o colaborador vinculado ao usuário autenticado.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Não existe um colaborador vinculado a esta conta."
    }
  
    // Impede que um colaborador desligado altere o perfil.
    var $status_colaborador {
      value = $colaborador.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado não pode alterar o perfil."
    }
  
    // Normaliza o e-mail pessoal.
    var $email_pessoal_normalizado {
      value = $input.email_pessoal|trim|to_lower
    }
  
    // Verifica se o e-mail pessoal está vinculado
    // a outro colaborador.
    db.get colaborador {
      field_name = "email_pessoal"
      field_value = $email_pessoal_normalizado
    } as $colaborador_mesmo_email
  
    precondition ($colaborador_mesmo_email == null || $colaborador_mesmo_email.id == $colaborador.id) {
      error_type = "inputerror"
      error = "Este e-mail pessoal já pertence a outro colaborador."
    }
  
    // Normaliza a sigla do estado.
    var $estado_normalizado {
      value = $input.estado|trim|to_upper
    }
  
    // Atualiza somente os dados pessoais permitidos.
    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador.id
      data = {
        email_pessoal: $email_pessoal_normalizado
        telefone     : $input.telefone
        cep          : $input.cep
        logradouro   : $input.logradouro
        numero       : $input.numero
        complemento  : $input.complemento
        bairro       : $input.bairro
        cidade       : $input.cidade
        estado       : $estado_normalizado
        updated_at   : "now"
      }
    } as $colaborador_atualizado
  }

  response = {
    sucesso    : true
    mensagem   : "Perfil atualizado com sucesso."
    colaborador: $colaborador_atualizado
  }

  guid = "6LiXzx5ZafLSgssXK-8V77bkg1Y"
}