// RH/ADMIN encerra uma pesquisa de clima: ela deixa de aceitar respostas
// (`perguntas_clima/{id}/responder` exige pesquisa ativa) e os resultados
// passam a poder ser consultados (`pesquisas_clima/{id}/resultados` so abre
// depois do encerramento). Auditado.
query "pesquisas_clima/{id}/encerrar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem encerrar pesquisas de clima."
    }

    db.get pesquisa_clima {
      field_name = "id"
      field_value = $input.id
    } as $pesquisa

    precondition ($pesquisa != null) {
      error_type = "notfound"
      error = "Pesquisa de clima nao encontrada."
    }

    precondition ($pesquisa.ativo) {
      error_type = "inputerror"
      error = "Esta pesquisa ja esta encerrada."
    }

    db.edit pesquisa_clima {
      field_name = "id"
      field_value = $pesquisa.id
      data = {
        ativo     : false
        updated_at: "now"
      }
    } as $pesquisa_encerrada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "encerrar_pesquisa_clima"
        recurso    : "pesquisa_clima"
        registro_id: $pesquisa.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Pesquisa de clima encerrada."
    pesquisa: $pesquisa_encerrada
  }

  guid = "conectahr-pesquisas-clima-encerrar-post-0001"
}
