// Solicitacao de redefinicao de senha (esqueci minha senha)
// Gera um codigo de uso unico e envia por e-mail. Nunca revela se o e-mail existe.
query "auth/senha/esqueci" verb=POST {
  api_group = "ConectaRH — Autenticação"

  input {
    email email filters=trim|lower
  }

  stack {
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $user
  
    // So gera e envia o codigo se a conta existir e estiver ativa,
    // mas a resposta e identica em qualquer caso (nao enumera contas).
    var $usuario_elegivel {
      value = ($user != null && $user.ativo)
    }
  
    conditional {
      if ($usuario_elegivel) {
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
            reset_senha_codigo    : $codigo_texto
            reset_senha_expira_em : now|add_secs_to_timestamp:900
            reset_senha_tentativas: 0
            updated_at            : "now"
          }
        } as $user_com_reset
      
        // Envio via Brevo usando o template transacional
        // "conectahr_redefinicao_senha" (id 4 — ver docs/emails-templates.md).
        api.request {
          url = "https://api.brevo.com/v3/smtp/email"
          method = "POST"
          params = {
            to        : [{email: $user.email, name: $user.nome}]
            templateId: 4
            params    : {nome: $user.nome, codigo: $codigo_texto}
          }

          headers = [
            "Content-Type: application/json"
            "api-key: " ~ $env.BREVO_API_KEY
          ]
        } as $resposta_brevo

        var $email_enviado {
          value = ($resposta_brevo.response.status >= 200 && $resposta_brevo.response.status < 300)
        }
      
        precondition ($email_enviado) {
          error = "Nao foi possivel enviar o codigo de redefinicao. Tente novamente em instantes."
        }
      
        // Auditoria: solicitacao de redefinicao de senha (nunca o codigo em si).
        db.add auditoria {
          data = {
            user_id    : $user.id
            acao       : "solicitar_redefinicao_senha"
            recurso    : "user"
            registro_id: $user.id
            resultado  : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    mensagem: "Se o e-mail informado estiver cadastrado, enviamos um codigo de redefinicao de senha."
  }

  guid = "conectahr-auth-senha-esqueci-0001"
}