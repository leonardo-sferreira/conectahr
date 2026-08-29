// Gera um novo codigo de OTP de 6 digitos para o usuario informado,
// grava com expiracao de 5 minutos e zera as tentativas, e envia por
// e-mail via SendGrid. Reaproveitada pelo login e pelo reenvio de codigo.
function "ConectaHR/emitir_otp_login" {
  input {
    int user_id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $input.user_id
    } as $usuario

    precondition ($usuario != null) {
      error_type = "notfound"
      error = "Usuario nao encontrado."
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
      field_value = $usuario.id
      data = {
        otp_codigo    : $codigo_texto
        otp_expira_em : now|add_secs_to_timestamp:300
        otp_tentativas: 0
        updated_at    : "now"
      }
    } as $usuario_atualizado

    // Envia o codigo por e-mail via SendGrid diretamente
    // (function.run entre functions nao resolve de forma confiavel
    // neste workspace, ver conectahr-xano-platform-quirks).
    api.request {
      url = "https://api.sendgrid.com/v3/mail/send"
      method = "POST"
      headers = ["Content-Type: application/json", "Authorization: Bearer " ~ $env.SENDGRID_API_KEY]
      params = {
        personalizations: [
          {
            to: [{email: $usuario.email, name: $usuario.nome}]
          }
        ]
        from: {email: "conecta.rh.retorno@gmail.com", name: "ConectaRH"}
        subject: "Seu codigo de acesso ConectaRH"
        content: [
          {
            type : "text/plain"
            value: "Ola, " ~ $usuario.nome ~ ". Seu codigo de acesso ao ConectaRH e " ~ $codigo_texto ~ ". Ele expira em 5 minutos. Se voce nao tentou entrar no ConectaRH, ignore este e-mail."
          }
        ]
      }
    } as $resposta_sendgrid

    var $sucesso_envio {
      value = ($resposta_sendgrid.response.status >= 200 && $resposta_sendgrid.response.status < 300)
    }
  }

  response = {
    sucesso    : $sucesso_envio
    status_code: $resposta_sendgrid.response.status
  }

  tags = ["conectahr"]
  guid = "conectahr-emitir-otp-login-0001"
}
