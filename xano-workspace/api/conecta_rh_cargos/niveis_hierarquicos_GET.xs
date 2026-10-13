// Niveis hierarquicos da empresa, da ordem menor (topo) para a maior (change organograma-hierarquia,
// D3). Qualquer perfil logado consulta: o organograma e publico. So o RH e o Admin veem os inativos.
query niveis_hierarquicos verb=GET {
  api_group = "ConectaRH — Cargos"
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

    var $ve_inativos {
      value = (($usuario_autenticado.perfil|trim|to_upper) == "RH" || ($usuario_autenticado.perfil|trim|to_upper) == "ADMIN")
    }

    db.query nivel_hierarquico {
      sort = {nivel_hierarquico.ordem: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "ordem", "ativo"]
    } as $todos

    var $niveis {
      value = []
    }

    foreach ($todos) {
      each as $n {
        conditional {
          if ($n.ativo || $ve_inativos) {
            var.update $niveis {
              value = $niveis|push:$n
            }
          }
        }
      }
    }
  }

  response = {
    sucesso: true
    niveis : $niveis
  }

  guid = "conectahr-niveis-hierarquicos-get-0001"
}
