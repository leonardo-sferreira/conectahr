// Redefinicao de senha via codigo de uso unico enviado por e-mail (fluxo "esqueci minha senha").
query "auth/senha/redefinir" verb=POST {
  api_group = "ConectaRH — Autenticação"

  input {
    email email filters=trim|lower
    text codigo filters=trim|max:6
    text nova_senha filters=min:8|max:64
    text confirmar_senha filters=min:8|max:64
  }

  stack {
    // Validacao de forma pura, antes de qualquer consulta — nao pode vazar,
    // via diferenca de mensagem de erro, se existe um desafio de redefinicao
    // pendente para o e-mail informado.
    precondition ($input.nova_senha == $input.confirmar_senha) {
      error_type = "inputerror"
      error = "A confirmacao nao corresponde a nova senha."
    }

    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $user

    // Nao revela se o e-mail existe.
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "Codigo invalido ou expirado."
    }

    precondition ($user.ativo) {
      error_type = "accessdenied"
      error = "Codigo invalido ou expirado."
    }

    // Precisa existir um desafio de redefinicao pendente.
    precondition ($user.reset_senha_codigo != null) {
      error_type = "accessdenied"
      error = "Codigo invalido ou expirado."
    }

    // Bloqueia apos muitas tentativas erradas; exige nova solicitacao.
    precondition ($user.reset_senha_tentativas < 5) {
      error_type = "toomanyrequests"
      error = "Muitas tentativas invalidas. Solicite um novo codigo de redefinicao."
    }

    // Bloqueia codigo expirado.
    precondition ($user.reset_senha_expira_em > now) {
      error_type = "accessdenied"
      error = "Codigo invalido ou expirado."
    }

    var $codigo_correto {
      value = ($input.codigo == $user.reset_senha_codigo)
    }
  
    // Registra a tentativa invalida e recusa sem revelar o motivo exato.
    conditional {
      if ($codigo_correto == false) {
        db.edit user {
          field_name = "id"
          field_value = $user.id
          data = {
            reset_senha_tentativas: $user.reset_senha_tentativas + 1
            updated_at            : "now"
          }
        } as $user_tentativa_invalida
      
        // Auditoria: tentativa de redefinicao com codigo invalido (nunca o codigo).
        db.add auditoria {
          data = {
            user_id    : $user.id
            acao       : "redefinicao_senha_codigo_invalido"
            recurso    : "user"
            registro_id: $user.id
            resultado  : "falha"
          }
        } as $evento_auditoria_falha
      
        precondition (false) {
          error_type = "accessdenied"
          error = "Codigo invalido ou expirado."
        }
      }
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
  
    // Grava a nova senha, encerra o desafio (uso unico) e conclui o primeiro acesso.
    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {
        senha                 : $input.nova_senha
        senha_primeiro_acesso : false
        reset_senha_codigo    : null
        reset_senha_expira_em : null
        reset_senha_tentativas: 0
        updated_at            : "now"
      }
    } as $user_atualizado
  
    // Auditoria: redefinicao concluida com sucesso (nunca a senha em si).
    db.add auditoria {
      data = {
        user_id    : $user.id
        acao       : "redefinir_senha_sucesso"
        recurso    : "user"
        registro_id: $user.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Senha redefinida com sucesso. Faca login com a nova senha."
  }

  guid = "conectahr-auth-senha-redefinir-0001"
}