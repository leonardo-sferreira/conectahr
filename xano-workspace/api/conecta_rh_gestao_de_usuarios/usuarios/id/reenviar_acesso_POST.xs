// Reenvia o acesso a quem ainda não trocou a senha temporária (tela "Usuários e perfis", Figma 246:612; tarefa 76 da
// change concluir-frontend-streamlit). Só ADMIN, nunca na própria conta, e só para conta ativa que ainda usa a senha
// temporária. Grava a nova senha temporária (que a tela gera, como no "Criar acesso"), tira o bloqueio de tentativas,
// manda a senha por e-mail e registra na auditoria, sem a senha.
query "usuarios/{id}/reenviar_acesso" verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    text senha_temporaria filters=min:8|max:64
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }
  
    // Impede o uso por uma conta inativa.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil do usuário autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente ADMIN pode reenviar acessos."
    }

    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_alvo

    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    precondition ($usuario_alvo.id != $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Você não pode fazer isso na própria conta."
    }

    precondition ($usuario_alvo.ativo) {
      error_type = "inputerror"
      error = "A conta está inativa: reative antes de reenviar o acesso."
    }

    precondition ($usuario_alvo.senha_primeiro_acesso) {
      error_type = "inputerror"
      error = "Esta pessoa já trocou a senha temporária. Se esqueceu a senha, ela usa Esqueci minha senha."
    }

    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {senha: $input.senha_temporaria, senha_primeiro_acesso: true, senha_tentativas_invalidas: 0, senha_bloqueada_ate: null, updated_at: "now"}
    } as $usuario_atualizado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "reenviar_acesso"
        recurso    : "user"
        registro_id: $usuario_alvo.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    // Mesmo modelo do "Criar acesso" (template generico id 1). A senha nunca vai para a auditoria nem para o log.
    api.request {
      url = "https://api.brevo.com/v3/smtp/email"
      method = "POST"
      headers = ["Content-Type: application/json", "api-key: " ~ $env.BREVO_API_KEY]
      params = {
        to        : [{email: $usuario_alvo.email, name: $usuario_alvo.nome}]
        templateId: 1
        params    : {
          nome    : $usuario_alvo.nome
          titulo  : "Seu acesso ao ConectaRH"
          mensagem: "Enviamos uma nova senha temporaria para a sua conta no ConectaRH. Entre com o e-mail " ~ $usuario_alvo.email ~ " e a senha temporaria " ~ $input.senha_temporaria ~ ". No primeiro acesso voce troca a senha. A senha temporaria anterior deixou de valer."
        }
      }
    } as $resposta_email

    var $email_enviado {
      value = ($resposta_email.response.status >= 200 && $resposta_email.response.status < 300)
    }
  }

  response = {
    sucesso      : true
    mensagem     : "Nova senha temporária enviada."
    email_enviado: $email_enviado
  }

  guid = "conectahr-usuarios-reenviar-acesso-post-0001"
}
