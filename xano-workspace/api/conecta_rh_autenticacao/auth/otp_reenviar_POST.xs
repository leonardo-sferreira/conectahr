// Reenvia um novo codigo OTP por e-mail, substituindo o anterior.
// Uso quando o codigo expirou ou o e-mail nao chegou. Nao zera as tentativas
// erradas; limite de 3 reenvios por login e intervalo minimo de 60s.
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

    // Depois de 5 codigos errados, so um novo login gera outro codigo.
    precondition ($user.otp_tentativas == null || $user.otp_tentativas < 5) {
      error_type = "toomanyrequests"
      error = "Nao foi possivel reenviar o codigo. Faca login novamente."
    }

    // No maximo 3 reenvios por login.
    precondition ($user.otp_reenvios == null || $user.otp_reenvios < 3) {
      error_type = "toomanyrequests"
      error = "Nao foi possivel reenviar o codigo. Faca login novamente."
    }

    // Intervalo minimo de 60 segundos entre envios.
    precondition ($user.otp_ultimo_envio_em == null || ($user.otp_ultimo_envio_em|add_secs_to_timestamp:60) <= now) {
      error_type = "toomanyrequests"
      error = "Aguarde um minuto antes de pedir um novo codigo."
    }

    security.random_number {
      min = 100000
      max = 999999
    } as $codigo_numerico

    var $codigo_texto {
      value = $codigo_numerico|to_text
    }

    // So o hash (HMAC-SHA256) do codigo vai para o banco; o texto so segue por e-mail.
    function.run "ConectaHR/hash_codigo_acesso" {
      input = {user_id: $user.id, codigo: $codigo_texto}
    } as $codigo_hash

    db.edit user {
      field_name = "id"
      field_value = $user.id
      data = {
        otp_codigo         : $codigo_hash
        otp_expira_em      : now|add_secs_to_timestamp:300
        otp_reenvios       : ($user.otp_reenvios == null ? 1 : $user.otp_reenvios + 1)
        otp_ultimo_envio_em: "now"
        updated_at         : "now"
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
