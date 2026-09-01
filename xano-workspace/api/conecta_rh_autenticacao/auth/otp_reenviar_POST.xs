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

    // Envio via Brevo usando o template transacional
    // "conectahr_codigo_acesso_reenvio" (id 3 — ver docs/emails-templates.md).
    api.request {
      url = "https://api.brevo.com/v3/smtp/email"
      method = "POST"
      headers = ["Content-Type: application/json", "api-key: " ~ $env.BREVO_API_KEY]
      params = {
        to        : [{email: $user.email, name: $user.nome}]
        templateId: 3
        params    : {nome: $user.nome, codigo: $codigo_texto}
      }
    } as $resposta_brevo

    var $email_enviado {
      value = ($resposta_brevo.response.status >= 200 && $resposta_brevo.response.status < 300)
    }

    precondition ($email_enviado) {
      error_type = "standard"
      error = "Nao foi possivel enviar o codigo de acesso. Tente novamente em instantes."
    }

    // Auditoria: reenvio do codigo de acesso (nunca o codigo em si).
    db.add auditoria {
      data = {
        user_id    : $user.id
        acao       : "codigo_acesso_reenviado"
        recurso    : "user"
        registro_id: $user.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    aguardando_otp: true
    mensagem      : "Enviamos um novo codigo de 6 digitos para o seu e-mail cadastrado."
  }

  guid = "conectahr-auth-otp-reenviar-0001"
}
