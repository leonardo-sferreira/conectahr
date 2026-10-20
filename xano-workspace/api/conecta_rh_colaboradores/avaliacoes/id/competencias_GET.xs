// Formulario de uma avaliacao para o avaliador designado (change
// trajetoria-do-colaborador, D3): as competencias ativas do nivel do avaliado
// (todas as ativas, se o nivel nao tiver nenhuma) e as respostas ja salvas.
// Avaliacao inexistente e avaliador errado dao o mesmo erro, para nao revelar
// se a avaliacao existe. So leitura.
query "avaliacoes/{id}/competencias" verb=GET {
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

    db.get avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $avaliacao_atual

    precondition (($avaliacao_atual != null) && ($avaliacao_atual.user_id == $usuario_autenticado.id)) {
      error_type = "accessdenied"
      error = "Somente o avaliador designado pode responder esta avaliacao."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $avaliacao_atual.colaborador_id
      output = ["id", "nome", "nivel"]
    } as $avaliado

    var $nivel_avaliado {
      value = ($avaliado != null ? $avaliado.nivel : null)
    }

    db.query competencia_avaliacao {
      where = $db.competencia_avaliacao.nivel == $nivel_avaliado && $db.competencia_avaliacao.ativo == true
      sort = {competencia_avaliacao.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "descricao", "categoria", "nivel"]
    } as $competencias

    conditional {
      if (($competencias|count) == 0) {
        db.query competencia_avaliacao {
          where = $db.competencia_avaliacao.ativo == true
          sort = {competencia_avaliacao.nome: "asc"}
          return = {type: "list"}
          output = ["id", "nome", "descricao", "categoria", "nivel"]
        } as $todas_ativas

        var.update $competencias {
          value = $todas_ativas
        }
      }
    }

    db.query resposta_avaliacao {
      where = $db.resposta_avaliacao.avaliacao_id == $avaliacao_atual.id
      return = {type: "list"}
      output = ["id", "competencia_avaliacao_id", "nota", "comentario"]
    } as $respostas
  }

  response = {
    sucesso      : true
    avaliacao_id : $avaliacao_atual.id
    status       : $avaliacao_atual.status
    relacao      : $avaliacao_atual.relacao_avaliador
    avaliado_nome: ($avaliado != null ? $avaliado.nome : null)
    competencias : $competencias
    respostas    : $respostas
  }

  guid = "conectahr-avaliacoes-competencias-get-0001"
}
