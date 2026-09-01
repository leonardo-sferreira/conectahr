// Envia um e-mail transacional via Brevo (ate 2026-08-31 usava
// SendGrid; migrado porque a assinatura paga do SendGrid expirou —
// Brevo tem nivel gratuito permanente de 300 e-mails/dia).
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

    // Template transacional "conectahr_outbox_generico" (id 1 — ver
    // docs/emails-templates.md), mesmo template reutilizado pelo
    // processador de email_outbox.
    api.request {
      url = "https://api.brevo.com/v3/smtp/email"
      method = "POST"
      headers = ["Content-Type: application/json", "api-key: " ~ $env.BREVO_API_KEY]
      params = {
        to        : [{email: $input.destinatario, name: $nome_final}]
        templateId: 1
        params    : {nome: $nome_final, titulo: $input.assunto, mensagem: $input.corpo_texto}
      }
    } as $resposta_brevo

    var $sucesso {
      value = ($resposta_brevo.response.status >= 200 && $resposta_brevo.response.status < 300)
    }
  }

  response = {
    sucesso    : $sucesso
    status_code: $resposta_brevo.response.status
    corpo      : $resposta_brevo.response.result
  }

  tags = ["conectahr"]
  guid = "conectahr-enviar-email-0001"
}
