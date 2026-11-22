// Treinamentos da propria pessoa (change treinamentos-obrigatorios, D4): os ativos obrigatorios para ela (para
// todos ou para o departamento dela) e as conclusoes dela, com o nome do treinamento. As situacoes (em dia,
// vencendo, vencido, pendente) saem na tela. Com video (change treinamento-em-video): a fonte (Drive ou YouTube), o id, a duracao,
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
              value = $obrigatorios|push:{id: $t.id, nome: $t.nome, categoria: $t.categoria, carga_horas: $t.carga_horas, validade_meses: $t.validade_meses, video_drive_id: $t.video_drive_id, video_fonte: $t.video_fonte, video_duracao: $t.video_duracao, video_percentual_minimo: $t.video_percentual_minimo}
            }
          }
        }
      }
    }

    // Cards (change cards-de-treinamentos, D4): todos os ativos do publico da pessoa, obrigatorios e opcionais, com o
    // tipo de conteudo. O opcional entra como convite. Capas: URLs assinadas em "capas", uma lista de {caminho, url}
    // (o mapa do assinar_treinamentos aninha no ponto de "uuid.webp"; o get com o mesmo caminho le certo).
    var $cards {
      value = []
    }

    var $caminhos_capa {
      value = []
    }

    foreach ($ativos) {
      each as $tc {
        var $ids_card {
          value = ($tc.departamento_ids == null) ? "" : $tc.departamento_ids
        }

        conditional {
          if (($tc.publico == "todos") || ($ids_card|contains:$meu_departamento)) {
            var.update $cards {
              value = $cards|push:{id: $tc.id, nome: $tc.nome, descricao: $tc.descricao, categoria: $tc.categoria, carga_horas: $tc.carga_horas, validade_meses: $tc.validade_meses, obrigatorio: $tc.obrigatorio, conteudo_tipo: ($tc.conteudo_tipo == null ? "video" : $tc.conteudo_tipo), video_drive_id: $tc.video_drive_id, video_fonte: $tc.video_fonte, video_duracao: $tc.video_duracao, video_percentual_minimo: $tc.video_percentual_minimo, conteudo_url: $tc.conteudo_url, tem_arquivo: ($tc.conteudo_path != null), capa_path: $tc.capa_path}
            }

            conditional {
              if ($tc.capa_path != null) {
                var.update $caminhos_capa {
                  value = $caminhos_capa|push:$tc.capa_path
                }
              }
            }
          }
        }
      }
    }

    function.run "ConectaHR/assinar_treinamentos" {
      input = {caminhos: $caminhos_capa}
    } as $assinadas

    var $capas {
      value = []
    }

    foreach ($caminhos_capa) {
      each as $caminho_capa {
        var $url_capa {
          value = $assinadas|get:$caminho_capa
        }

        conditional {
          if ($url_capa != null) {
            var.update $capas {
              value = $capas|push:{caminho: $caminho_capa, url: $url_capa}
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
      output = ["treinamento_id", "segundos_vistos", "posicao", "aberto_em"]
    } as $progressos
  }

  response = {
    sucesso     : true
    hoje        : $hoje
    obrigatorios: $obrigatorios
    cards       : $cards
    capas       : $capas
    conclusoes  : $conclusoes
    progressos  : $progressos
  }

  guid = "conectahr-meus-treinamentos-get-0001"
}
