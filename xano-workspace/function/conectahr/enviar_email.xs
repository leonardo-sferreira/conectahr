// Envia um e-mail transacional via SendGrid.
// Uso sincrono (chamador espera o resultado) - adequado para fluxos
// onde o usuario esta aguardando ativamente. Notificacoes assincronas
// (decisoes de ferias, ausencia, etc.) devem usar o padrao de outbox
// definido no design.md do conectahr, nao esta function diretamente.
// ATENCAO: function.run chamando esta function a partir de outra
// function nao resolveu de forma confiavel neste workspace (ver
// conectahr-xano-platform-quirks). O login (auth/login_POST.xs) e o
// reenvio de OTP duplicam esta logica inline em vez de chamar esta
// function por seguranca. Prefira chamar esta function so a partir de
// uma query (endpoint), nao de outra function, ate o motivo raiz do
// problema ser confirmado.
function "ConectaHR/enviar_email" {
  input {
    email destinatario
    text nome_destinatario? filters=trim
    text assunto filters=trim|max:200
    text corpo_texto filters=trim
  }

  stack {
    var $nome_final {
      value = ($input.nome_destinatario != null ? $input.nome_destinatario : $input.destinatario)
    }

    api.request {
      url = "https://api.sendgrid.com/v3/mail/send"
      method = "POST"
      headers = ["Content-Type: application/json", "Authorization: Bearer " ~ $env.SENDGRID_API_KEY]
      params = {
        personalizations: [
          {
            to: [{email: $input.destinatario, name: $nome_final}]
          }
        ]
        from: {email: "conecta.rh.retorno@gmail.com", name: "ConectaRH"}
        subject: $input.assunto
        content: [
          {type: "text/plain", value: $input.corpo_texto}
        ]
      }
    } as $resposta_sendgrid

    var $sucesso {
      value = ($resposta_sendgrid.response.status >= 200 && $resposta_sendgrid.response.status < 300)
    }
  }

  response = {
    sucesso    : $sucesso
    status_code: $resposta_sendgrid.response.status
    corpo      : $resposta_sendgrid.response.result
  }

  tags = ["conectahr"]
  guid = "conectahr-enviar-email-0001"
}
