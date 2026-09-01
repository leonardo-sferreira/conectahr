// Autenticação de usuário do ConectaRH
// Autentica um usuário ativo e retorna o token e a situação do primeiro acesso.
query "auth/login" verb=POST {
  api_group = "ConectaRH — Autenticação"

  input {
    email email filters=trim|lower
    text password
  }

  stack {
    // Carrega o usuário completo, incluindo a senha protegida.
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $user
  
    // Não revela se o e-mail existe.
    precondition ($user != null) {
      error_type = "accessdenied"
      error = "E-mail ou senha inválidos."
    }
  
    // Bloqueia contas desativadas.
    precondition ($user.ativo) {
      error_type = "accessdenied"
      error = "E-mail ou senha inválidos."
    }

    // Bloqueio temporario por tentativas invalidas de senha (mesmo padrao
    // ja usado para OTP e redefinicao de senha). Mesmo trade-off de design
    // ja aceito em auth/senha/redefinir: a mensagem especifica revela que
    // ha uma conta com tentativas recentes, mas isso ja e o comportamento
    // padrao deste projeto para bloqueio por tentativas.
    precondition ($user.senha_bloqueada_ate == null || $user.senha_bloqueada_ate < now) {
      error_type = "toomanyrequests"
      error = "Muitas tentativas invalidas. Tente novamente em alguns minutos."
    }

    // Compara a senha informada com o hash armazenado.
    security.check_password {
      text_password = $input.password
      hash_password = $user.senha
    } as $pass_result

    // Senha errada: registra a tentativa e bloqueia temporariamente apos
    // 5 tentativas invalidas seguidas (15 minutos, mesma janela usada na
    // redefinicao de senha).
    conditional {
      if ($pass_result == false) {
        var $tentativas_atuais {
          value = ($user.senha_tentativas_invalidas != null ? $user.senha_tentativas_invalidas : 0)
        }

        var $nova_tentativa {
          value = ($tentativas_atuais + 1)
        }

        var $deve_bloquear {
          value = ($nova_tentativa >= 5)
        }

        var $bloqueio_ate {
          value = ($deve_bloquear ? (now|add_secs_to_timestamp:900) : null)
        }

        db.edit user {
          field_name = "id"
          field_value = $user.id
          data = {
            senha_tentativas_invalidas: $nova_tentativa
            senha_bloqueada_ate       : $bloqueio_ate
            updated_at                : "now"
          }
        } as $user_tentativa_invalida

        // Auditoria: tentativa de login com senha invalida.
        db.add auditoria {
          data = {
            user_id    : $user.id
            acao       : "login_senha_invalida"
            recurso    : "user"
            registro_id: $user.id
            resultado  : "falha"
          }
        } as $evento_auditoria_senha_invalida
      }
    }

    precondition ($pass_result) {
      error_type = "accessdenied"
      error = "E-mail ou senha inválidos."
    }

    // Alerta de acesso suspeito (item 7.9): login bem-sucedido logo apos
    // varias tentativas de senha invalida sugere uma tentativa de forca
    // bruta que acabou acertando — notifica o titular por e-mail via
    // outbox assincrono (nao atrasa nem falha o login em si).
    conditional {
      if ($user.senha_tentativas_invalidas != null && $user.senha_tentativas_invalidas >= 3) {
        db.add email_outbox {
          data = {
            destinatario_email: $user.email
            destinatario_nome : $user.nome
            assunto           : "ConectaRH - Alerta de seguranca na sua conta"
            corpo             : "Ola " ~ $user.nome ~ ",\n\nDetectamos " ~ ($user.senha_tentativas_invalidas|to_text) ~ " tentativas de acesso com senha incorreta na sua conta, seguidas de um login bem-sucedido agora. Se foi voce, pode ignorar este aviso. Se nao reconhece essa atividade, troque sua senha imediatamente e contate o RH.\n\nEste e um aviso automatico de seguranca."
            chave_idempotencia: ("alerta_acesso_suspeito_" ~ ($user.id|to_text) ~ "_" ~ (now|to_text))
          }
        } as $alerta_seguranca_criado

        db.add auditoria {
          data = {
            user_id    : $user.id
            acao       : "alerta_acesso_suspeito"
            recurso    : "user"
            registro_id: $user.id
            justificativa: (($user.senha_tentativas_invalidas|to_text) ~ " tentativas de senha invalida antes do login bem-sucedido")
            resultado  : "sucesso"
          }
        } as $evento_auditoria_alerta
      }
    }

    // Senha correta: zera o contador de tentativas invalidas.
    conditional {
      if ($user.senha_tentativas_invalidas != null && $user.senha_tentativas_invalidas > 0) {
        db.edit user {
          field_name = "id"
          field_value = $user.id
          data = {
            senha_tentativas_invalidas: 0
            senha_bloqueada_ate       : null
          }
        } as $user_tentativas_zeradas
      }
    }

    // Gera e envia o codigo de acesso de 6 digitos por e-mail (OTP).
    // Validacao padrao de login do ConectaRH.
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
    } as $user_com_otp

    // Envio via Brevo, conteudo direto (a conta Brevo nao tem um
    // template equivalente ao Dynamic Template do SendGrid usado antes
    // — migrado em 2026-08-31 apos a assinatura paga do SendGrid
    // expirar).
    api.request {
      url = "https://api.brevo.com/v3/smtp/email"
      method = "POST"
      headers = ["Content-Type: application/json", "api-key: " ~ $env.BREVO_API_KEY]
      params = {
        sender     : {email: "conecta.rh.retorno@gmail.com", name: "ConectaRH"}
        to         : [{email: $user.email, name: $user.nome}]
        subject    : "Seu codigo de acesso ConectaRH"
        textContent: "Ola " ~ $user.nome ~ ",\n\nSeu codigo de acesso e: " ~ $codigo_texto ~ "\n\nEle expira em 5 minutos.\n\nSe voce nao solicitou este codigo, ignore este e-mail."
      }
    } as $resposta_brevo

    var $email_enviado {
      value = ($resposta_brevo.response.status >= 200 && $resposta_brevo.response.status < 300)
    }

    precondition ($email_enviado) {
      error_type = "standard"
      error = "Nao foi possivel enviar o codigo de acesso. Tente novamente em instantes."
    }

    // Auditoria: geracao do codigo de acesso (nunca o codigo em si).
    db.add auditoria {
      data = {
        user_id  : $user.id
        acao     : "codigo_acesso_gerado"
        recurso  : "user"
        registro_id: $user.id
        resultado: "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    aguardando_otp: true
    mensagem      : "Senha valida. Enviamos um codigo de 6 digitos para o seu e-mail cadastrado."
    email         : $user.email
  }

  guid = "ODyvwjfBqn40N51ETK1huleI1CM"
}