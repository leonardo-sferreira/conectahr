// Treinamentos da propria pessoa (change treinamentos-obrigatorios, D4): os ativos obrigatorios para ela (para
// todos ou para o departamento dela) e as conclusoes dela, com o nome do treinamento. As situacoes (em dia,
// vencendo, vencido, pendente) saem na tela. Com video (change treinamento-em-video): o id no Drive, a duracao,
// o minimo a assistir e o progresso da pessoa em cada um. Qualquer perfil com ficha.
query "meus_treinamentos" verb=GET {
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

    var $meu_departamento {
      value = "," ~ ($colaborador_autenticado.departamento_id|to_text) ~ ","
    }

    db.query treinamento {
      where = $db.treinamento.ativo == true
      sort = {treinamento.nome: "asc"}
      return = {type: "list"}
    } as $ativos

    var $obrigatorios {
      value = []
    }

    foreach ($ativos) {
      each as $t {
        var $ids_texto {
          value = ($t.departamento_ids == null) ? "" : $t.departamento_ids
        }

        conditional {
          if (($t.obrigatorio == true) && (($t.publico == "todos") || ($ids_texto|contains:$meu_departamento))) {
            var.update $obrigatorios {
              value = $obrigatorios|push:{id: $t.id, nome: $t.nome, categoria: $t.categoria, carga_horas: $t.carga_horas, validade_meses: $t.validade_meses, video_drive_id: $t.video_drive_id, video_duracao: $t.video_duracao, video_percentual_minimo: $t.video_percentual_minimo}
            }
          }
        }
      }
    }

    db.query treinamento_conclusao {
      where = $db.treinamento_conclusao.colaborador_id == $colaborador_autenticado.id
      sort = {treinamento_conclusao.concluido_em: "desc"}
      return = {type: "list"}
    } as $minhas

    var $conclusoes {
      value = []
    }

    foreach ($minhas) {
      each as $c {
        db.get treinamento {
          field_name = "id"
          field_value = $c.treinamento_id
          output = ["id", "nome", "carga_horas"]
        } as $tr

        var.update $conclusoes {
          value = $conclusoes|push:{treinamento_id: $c.treinamento_id, nome: ($tr != null ? $tr.nome : null), carga_horas: ($tr != null ? $tr.carga_horas : null), concluido_em: $c.concluido_em, valido_ate: $c.valido_ate, instrutor: $c.instrutor, certificado_url: $c.certificado_url}
        }
      }
    }

    db.query treinamento_progresso {
      where = $db.treinamento_progresso.colaborador_id == $colaborador_autenticado.id
      return = {type: "list"}
      output = ["treinamento_id", "segundos_vistos", "posicao"]
    } as $progressos
  }

  response = {
    sucesso     : true
    hoje        : $hoje
    obrigatorios: $obrigatorios
    conclusoes  : $conclusoes
    progressos  : $progressos
  }

  guid = "conectahr-meus-treinamentos-get-0001"
}
