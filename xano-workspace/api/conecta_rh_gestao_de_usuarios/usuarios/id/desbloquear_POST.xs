// Desbloqueia uma conta presa pelo bloqueio de tentativas de senha (tela "Usuários e perfis", Figma 246:612; tarefa 76
// da change concluir-frontend-streamlit). Só ADMIN, nunca na própria conta. Zera o contador e o fim do bloqueio; a senha
// não muda. O motivo vai para a auditoria.
query "usuarios/{id}/desbloquear" verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    text motivo filters=trim|min:5|max:500
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
      error = "Somente ADMIN pode desbloquear contas."
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

    precondition ($usuario_alvo.senha_bloqueada_ate != null && $usuario_alvo.senha_bloqueada_ate > now) {
      error_type = "inputerror"
      error = "Esta conta não está bloqueada."
    }

    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {senha_tentativas_invalidas: 0, senha_bloqueada_ate: null, updated_at: "now"}
    } as $usuario_desbloqueado

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "desbloquear_usuario"
        recurso      : "user"
        registro_id  : $usuario_alvo.id
        justificativa: $input.motivo
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Conta desbloqueada."
  }

  guid = "conectahr-usuarios-desbloquear-post-0001"
}
