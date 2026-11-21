// Sessoes ativas de todas as contas (tela "Sessoes ativas" do Admin, Figma 249:6819; tarefa 65 da change
// concluir-frontend-streamlit). So ADMIN. Devolve nome e perfil da conta, navegador e inicio; o IP nao sai daqui
// (minimizacao: o Admin encerra pela sessao, nao precisa do endereco).
query "admin/sessoes_ativas" verb=GET {
  api_group = "ConectaRH — Autenticação"
  auth = "user"

  input {
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

    db.query sessao {
      where = $db.sessao.ativa == true && $db.sessao.revogada_em == null && $db.sessao.expira_em > now
      sort = {sessao.created_at: "desc"}
      return = {type: "list"}
      output = ["id", "user_id", "created_at", "expira_em", "dispositivo"]
    } as $sessoes_abertas

    var $sessoes {
      value = []
    }

    foreach ($sessoes_abertas) {
      each as $s {
        db.get user {
          field_name = "id"
          field_value = $s.user_id
        } as $dono

        var.update $sessoes {
          value = $sessoes|push:{id: $s.id, user_id: $s.user_id, nome: ($dono != null ? $dono.nome : null), perfil: ($dono != null ? $dono.perfil : null), dispositivo: $s.dispositivo, created_at: $s.created_at, expira_em: $s.expira_em, atual: ($s.id == $sessao_token.id)}
        }
      }
    }
  }

  response = {
    sucesso        : true
    sessoes        : $sessoes
    sessao_atual_id: $sessao_token.id
  }

  guid = "conectahr-admin-sessoes-ativas-get-0001"
}
