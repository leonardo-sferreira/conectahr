// Solicitacao de redefinicao de senha (esqueci minha senha), usada tambem pelo
// "Reenviar codigo" da tela de redefinicao. Gera um codigo de uso unico e envia
// por e-mail. Nunca revela se o e-mail existe.
// Enquanto ha um codigo pendente (nao expirado), um novo pedido substitui o
// codigo sem zerar as tentativas erradas, respeita intervalo minimo de 60s e e
// ignorado depois de 5 tentativas erradas - o mesmo criterio do reenvio de OTP.
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

    // Cada comparacao fica entre parenteses proprios: sem isso o `&&` e
    // avaliado antes do `>` e a regra de intervalo deixa de valer (achado no
    // teste de 2026-10-07).
    var $agora {
      value = now
    }

    // O codigo vale 900s; expirar depois de agora+840s significa que foi
    // enviado ha menos de 60s.
    var $limite_reenvio {
      value = $agora|add_secs_to_timestamp:840
    }

    // Codigo anterior ainda valido: este pedido e um reenvio.
    var $codigo_pendente {
      value = (($usuario_elegivel) && ($user.reset_senha_codigo != null) && ($user.reset_senha_expira_em != null) && ($user.reset_senha_expira_em > $agora))
    }

    var $reenvio_cedo_demais {
      value = (($codigo_pendente) && ($user.reset_senha_expira_em > $limite_reenvio))
    }

    // Depois de 5 codigos errados, so vale um novo pedido apos o codigo expirar.
    var $tentativas_esgotadas {
      value = (($codigo_pendente) && ($user.reset_senha_tentativas != null) && ($user.reset_senha_tentativas >= 5))
    }

    var $deve_enviar {
      value = (($usuario_elegivel) && ($reenvio_cedo_demais == false) && ($tentativas_esgotadas == false))
    }

    var $tentativas_mantidas {
      value = ((($codigo_pendente) && ($user.reset_senha_tentativas != null)) ? $user.reset_senha_tentativas : 0)
    }

    conditional {
      if ($deve_enviar) {
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
            reset_senha_codigo    : $codigo_hash
            reset_senha_expira_em : now|add_secs_to_timestamp:900
            reset_senha_tentativas: $tentativas_mantidas
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