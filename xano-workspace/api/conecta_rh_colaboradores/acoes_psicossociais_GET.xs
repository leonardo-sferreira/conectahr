// Plano de acao dos riscos psicossociais (NR-1; change riscos-psicossociais, D3): as acoes de uma avaliacao
// (ou de todas, sem `pesquisa_id`), com setor, dimensao, nivel do risco, medida, responsavel, prazo e situacao.
// So RH e Admin.
query "acoes_psicossociais" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int? pesquisa_id?
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    // "!= null" trata 0 como nulo nesta plataforma: compara como texto.
    var $filtro_texto {
      value = $input.pesquisa_id|to_text
    }

    db.query acao_psicossocial {
      sort = {acao_psicossocial.prazo: "asc"}
      return = {type: "list"}
    } as $todas

    var $acoes {
      value = []
    }

    foreach ($todas) {
      each as $a {
        conditional {
          if (($filtro_texto == "") || (($a.pesquisa_clima_id|to_text) == $filtro_texto)) {
            var.update $acoes {
              value = $acoes|push:{id: $a.id, pesquisa_id: $a.pesquisa_clima_id, departamento_id: $a.departamento_id, dimensao: $a.dimensao, nivel_risco: $a.nivel_risco, medida: $a.medida, responsavel: $a.responsavel, prazo: $a.prazo, status: $a.status, concluida_em: $a.concluida_em}
            }
          }
        }
      }
    }
  }

  response = {
    sucesso: true
    hoje   : $hoje
    acoes  : $acoes
  }

  guid = "conectahr-acoes-psicossociais-get-0001"
}
