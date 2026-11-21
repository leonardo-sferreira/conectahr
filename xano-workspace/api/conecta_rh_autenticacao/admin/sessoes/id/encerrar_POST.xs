// O Admin encerra a sessao de qualquer conta (tela "Sessoes ativas", Figma 249:6819; tarefa 65 da change
// concluir-frontend-streamlit). A sessao do proprio token nao: para ela existe "Sair". Fica na auditoria.
query "admin/sessoes/{id}/encerrar" verb=POST {
  api_group = "ConectaRH — Autenticação"
  auth = "user"

  input {
    int id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente ADMIN pode ver e encerrar as sessoes de outras pessoas."
    }

    db.get sessao {
      field_name = "id"
      field_value = $input.id
    } as $sessao_alvo

    precondition ($sessao_alvo != null) {
      error_type = "notfound"
      error = "Sessao nao encontrada."
    }

    precondition ($sessao_alvo.id != $sessao_token.id) {
      error_type = "inputerror"
      error = "Esta e a sua sessao atual: use Sair."
    }

    precondition ($sessao_alvo.ativa && $sessao_alvo.revogada_em == null) {
      error_type = "inputerror"
      error = "Esta sessao ja esta encerrada."
    }

    db.edit sessao {
      field_name = "id"
      field_value = $sessao_alvo.id
      data = {ativa: false, revogada_em: "now", updated_at: "now"}
    } as $sessao_encerrada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "encerrar_sessao_admin"
        recurso    : "sessao"
        registro_id: $sessao_alvo.id
        justificativa: "user_id=" ~ ($sessao_alvo.user_id|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Sessao encerrada."
  }

  guid = "conectahr-admin-sessoes-encerrar-post-0001"
}
