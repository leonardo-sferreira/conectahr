// Reenvia um novo codigo OTP por e-mail, substituindo o anterior.
// Uso quando o codigo expirou ou o e-mail nao chegou.
query "auth/otp/reenviar" verb=POST {
  api_group = "ConectaRH — Autenticação"

  input {
    email email filters=trim|lower
  }

  stack {
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $user

    // Nao revela se o e-mail existe.
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "Nao foi possivel reenviar o codigo."
    }

    precondition ($user.ativo) {
      error_type = "accessdenied"
      error = "Nao foi possivel reenviar o codigo."
    }

    // So reenvia quando ha um desafio de OTP pendente (login com senha ja validado).
    precondition ($user.otp_codigo != null) {
      error_type = "accessdenied"
      error = "Nao foi possivel reenviar o codigo."
    }

    security.random_number {
      min = 100000
      max = 999999
    } as $codigo_numerico

    var $codigo_texto {
      value = $codigo_numerico|to_text
    }

    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {
        otp_codigo    : $codigo_texto
        otp_expira_em : now|add_secs_to_timestamp:300
        otp_tentativas: 0
        updated_at    : "now"
      }
    } as $user_com_novo_otp

    // Usa o Dynamic Template do SendGrid (email-templates/02-codigo-verificacao.html).
    api.request {
      url = "https://api.sendgrid.com/v3/mail/send"
      method = "POST"
      headers = ["Content-Type: application/json", "Authorization: Bearer " ~ $env.SENDGRID_API_KEY]
      params = {
        personalizations: [
          {
            to                    : [{email: $user.email, name: $user.nome}]
            dynamic_template_data : {
              first_name         : $user.nome
              verification_code  : $codigo_texto
              expires_in_minutes : "5"
              logo_url           : ""
              preheader_text     : "Seu novo codigo de acesso ConectaRH"
              unsubscribe_url    : "#"
              preferences_url    : "#"
            }
          }
        ]
        from       : {email: "conecta.rh.retorno@gmail.com", name: "ConectaRH"}
        template_id: "d-c595a07353ae46e18d9f9476f2420f5a"
      }
    } as $resposta_sendgrid

    var $email_enviado {
      value = ($resposta_sendgrid.response.status >= 200 && $resposta_sendgrid.response.status < 300)
    }

    precondition ($email_enviado) {
      error_type = "standard"
      error = "Nao foi possivel enviar o codigo de acesso. Tente novamente em instantes."
    }
  }

  response = {
    aguardando_otp: true
    mensagem      : "Enviamos um novo codigo de 6 digitos para o seu e-mail cadastrado."
  }

  guid = "conectahr-auth-otp-reenviar-0001"
}
