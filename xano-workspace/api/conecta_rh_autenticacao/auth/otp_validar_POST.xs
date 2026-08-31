// Valida o codigo OTP de 6 digitos enviado por e-mail e emite o token de sessao.
// Segundo passo do login, apos a senha ja ter sido validada em auth/login.
query "auth/otp/validar" verb=POST {
  api_group = "ConectaRH — Autenticação"

  input {
    email email filters=trim|lower
    text codigo filters=trim|max:6
  }

  stack {
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

    // Precisa existir um desafio de OTP pendente.
    precondition ($user.otp_codigo != null) {
      error_type = "accessdenied"
      error = "Codigo invalido ou expirado."
    }

    // Bloqueia apos muitas tentativas erradas; exige novo login.
    precondition ($user.otp_tentativas < 5) {
      error_type = "toomanyrequests"
      error = "Muitas tentativas invalidas. Faca login novamente para receber um novo codigo."
    }

    // Bloqueia codigo expirado.
    precondition ($user.otp_expira_em > now) {
      error_type = "accessdenied"
      error = "Codigo invalido ou expirado."
    }

    var $codigo_correto {
      value = ($input.codigo == $user.otp_codigo)
    }

    // Registra a tentativa invalida e recusa sem revelar o motivo exato.
    conditional {
      if ($codigo_correto == false) {
        db.edit user {
          field_name = "id"
          field_value = $user.id
          data = {otp_tentativas: $user.otp_tentativas + 1, updated_at: "now"}
        } as $user_tentativa_invalida

        // Auditoria: tentativa de login com codigo invalido (nunca o codigo).
        db.add auditoria {
          data = {
            user_id    : $user.id
            acao       : "login_codigo_invalido"
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

    // Codigo correto: limpa o desafio de OTP e atualiza o ultimo acesso.
    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {
        otp_codigo    : null
        otp_expira_em : null
        otp_tentativas: 0
        ultimo_acesso : "now"
        updated_at    : "now"
      }
    } as $user_validado

    // Procura o colaborador vinculado a conta.
    db.get colaborador {
      field_name = "user_id"
      field_value = $user.id
    } as $colaborador

    // Gera um token valido por uma hora.
    security.create_auth_token {
      table = "user"
      extras = {perfil: $user.perfil}
      expiration = 3600
      id = $user.id
    } as $auth_token

    // Registra a sessao para consulta e encerramento posterior
    // (item 2.2 / requisito "Sessoes e dispositivos").
    db.add sessao {
      data = {
        user_id  : $user.id
        expira_em: now|add_secs_to_timestamp:3600
        ativa    : true
      }
    } as $sessao_criada

    // Auditoria: login concluido com sucesso.
    db.add auditoria {
      data = {
        user_id    : $user.id
        acao       : "login_sucesso"
        recurso    : "user"
        registro_id: $user.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
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

  guid = "conectahr-auth-otp-validar-0001"
}
