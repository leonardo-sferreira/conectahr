// Lista regras de override, mais recentes primeiro.
query regras_override verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    db.query regra_override {
      sort = {regra_override.created_at: "desc"}
      return = {type: "list"}
    } as $todas

    // Conflitos das regras em rascunho ou pendentes (change tela-de-regras, D3); as demais vao sem.
    var $overrides {
      value = []
    }

    foreach ($todas) {
      each as $r {
        var $conflitos_regra {
          value = []
        }

        conditional {
          if (($r.status == "rascunho") || ($r.status == "pendente_aprovacao")) {
            function.run "ConectaHR/impacto_override" {
              input = {override_id: $r.id}
            } as $impacto_regra

            var.update $conflitos_regra {
              value = $impacto_regra.conflitos
            }
          }
        }

        var.update $overrides {
          value = $overrides|push:($r|set:"conflitos":$conflitos_regra)
        }
      }
    }
  }

  response = {
    sucesso  : true
    overrides: $overrides
  }

  guid = "conectahr-regras-override-get-0001"
}
