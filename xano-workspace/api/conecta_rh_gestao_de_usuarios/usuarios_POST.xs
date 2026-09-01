// Criação de acesso para um colaborador
// Cria uma conta de acesso para um colaborador. Operação exclusiva do RH.
query usuarios verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int colaborador_id
    email email filters=trim|lower
    text senha_temporaria filters=min:8|max:64
  }

  stack {
    // Identifica o usuário que está criando o acesso.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh
  
    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil do usuário autenticado.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // Somente Admin ou RH podem criar acessos.
    precondition ($perfil_rh == "RH" || $perfil_rh == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente Admin ou RH podem criar contas de acesso."
    }
  
    // Localiza o colaborador.
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
      output = ["id", "nome", "user_id", "status"]
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador não encontrado."
    }
  
    // Normaliza o status do colaborador.
    var $status_colaborador {
      value = $colaborador.status|trim|to_upper
    }
  
    // Colaborador desligado não pode receber acesso.
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Não é possível criar acesso para um colaborador desligado."
    }
  
    // Verifica se o user_id aponta para uma conta que realmente existe.
    // db.get com field_value nulo falha com "Missing param: field_value"
    // (nao retorna null graciosamente) — so consulta quando ha um
    // user_id de fato vinculado.
    var $usuario_ja_vinculado {
      value = null
    }

    conditional {
      if ($colaborador.user_id != null) {
        db.get user {
          field_name = "id"
          field_value = $colaborador.user_id
        } as $usuario_encontrado

        var.update $usuario_ja_vinculado {
          value = $usuario_encontrado
        }
      }
    }

    // Só bloqueia quando uma conta vinculada realmente foi encontrada.
    precondition ($usuario_ja_vinculado == null) {
      error_type = "inputerror"
      error = "Este colaborador já possui uma conta de acesso."
    }
  
    // Procura outra conta com o mesmo e-mail.
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $usuario_email_existente
  
    precondition ($usuario_email_existente == null) {
      error_type = "inputerror"
      error = "Este e-mail já está vinculado a outra conta."
    }
  
    // Cria a conta e vincula o colaborador na mesma transação.
    db.transaction {
      stack {
        db.add user {
          data = {
            nome                        : $colaborador.nome
            email                       : $input.email
            senha                       : $input.senha_temporaria
            ativo                       : true
            senha_primeiro_acesso: true
          }
        } as $novo_usuario
      
        db.edit colaborador {
          field_name = "id"
          field_value = $colaborador.id
          data = {user_id: $novo_usuario.id, updated_at: "now"}
        } as $colaborador_atualizado
      }
    }
  
    // Carrega somente os campos seguros da nova conta.
    db.get user {
      field_name = "email"
      field_value = $input.email
      output = [
        "id"
        "nome"
        "email"
        "perfil"
        "ativo"
        "senha_primeiro_acesso"
      ]
    } as $usuario_criado

    // Auditoria: criacao de conta de acesso (item 7.11). Nunca a senha em si.
    db.add auditoria {
      data = {
        user_id    : $usuario_rh.id
        acao       : "criar_conta_acesso"
        recurso    : "user"
        registro_id: $usuario_criado.id
        valor_novo : ("colaborador_id=" ~ ($colaborador.id|to_text) ~ "; email=" ~ $usuario_criado.email)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Conta de acesso criada com sucesso. O colaborador deve alterar a senha no primeiro login."
    usuario : ```
      {
        id: $usuario_criado.id
        nome: $usuario_criado.nome
        email: $usuario_criado.email
        perfil: $usuario_criado.perfil
        ativo: $usuario_criado.ativo
        colaborador_id: $colaborador.id
        senha_primeiro_acesso: $usuario_criado.senha_primeiro_acesso
      }
      ```
  }

  guid = "4w6MR47uPK1DAgZyQ84i2HNwlm4"
}