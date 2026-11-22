// Marca que a pessoa abriu o PDF ou a apresentacao (change cards-de-treinamentos, D6): grava aberto_em na primeira vez
// (a renovacao pede a abertura de novo, porque concluir zera). A tela chama ao mostrar o conteudo e antes de "Abrir em
// nova aba". So para quem esta no publico do treinamento ativo. Qualquer perfil com ficha.
query "meus_treinamentos/{id}/abrir" verb=POST {
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.get treinamento {
      field_name = "id"
      field_value = $input.id
    } as $treinamento

    var $meu_departamento {
      value = "," ~ ($colaborador_autenticado.departamento_id|to_text) ~ ","
    }

    var $ids_publico {
      value = ($treinamento == null || $treinamento.departamento_ids == null) ? "" : $treinamento.departamento_ids
    }

    // So quem esta no publico do treinamento ativo; os demais recebem 404, como se ele nao existisse.
    precondition (($treinamento != null) && ($treinamento.ativo == true) && (($treinamento.publico == "todos") || ($ids_publico|contains:$meu_departamento))) {
      error_type = "notfound"
      error = "Treinamento nao encontrado."
    }

    var $tipo_conteudo {
      value = ($treinamento.conteudo_tipo == null) ? "video" : $treinamento.conteudo_tipo
    }

    precondition ($tipo_conteudo != "video") {
      error_type = "inputerror"
      error = "Este treinamento e em video: o progresso conta pelo que a pessoa assiste."
    }

    db.query treinamento_progresso {
      where = $db.treinamento_progresso.treinamento_id == $treinamento.id && $db.treinamento_progresso.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $progresso

    var $aberto_em {
      value = ($progresso == null) ? null : $progresso.aberto_em
    }

    conditional {
      if ($progresso == null) {
        db.add treinamento_progresso {
          data = {
            treinamento_id : $treinamento.id
            colaborador_id : $colaborador_autenticado.id
            segundos_vistos: 0
            posicao        : 0
            aberto_em      : "now"
            atualizado_em  : "now"
          }
        } as $progresso_novo

        var.update $aberto_em {
          value = $progresso_novo.aberto_em
        }
      }

      elseif ($progresso.aberto_em == null) {
        db.edit treinamento_progresso {
          field_name = "id"
          field_value = $progresso.id
          data = {aberto_em: "now", atualizado_em: "now"}
        } as $progresso_aberto

        var.update $aberto_em {
          value = $progresso_aberto.aberto_em
        }
      }
    }
  }

  response = {
    sucesso  : true
    aberto_em: $aberto_em
  }

  guid = "conectahr-meus-treinamentos-abrir-post-0001"
}
