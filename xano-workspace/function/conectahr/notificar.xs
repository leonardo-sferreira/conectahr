// Cria uma notificacao interna para uma pessoa (sino do topo; parte 2 das notificacoes, 12/10/2026).
// A pessoa vem pelo usuario (destinatario_user_id) ou pelo colaborador (colaborador_id, que acha o
// usuario). Sem conta, ou quando o destinatario e o proprio autor da acao, nao cria nada.
function "ConectaHR/notificar" {
  input {
    int? destinatario_user_id?
    int? colaborador_id?
    int? autor_user_id?
    text tipo
    text titulo filters=trim|max:150
    text mensagem filters=trim|max:1000
    text recurso filters=trim|max:50
    int? registro_id?
  }

  stack {
    var $destino {
      value = $input.destinatario_user_id
    }

    conditional {
      if ($destino == null && $input.colaborador_id != null) {
        db.get colaborador {
          field_name = "id"
          field_value = $input.colaborador_id
        } as $pessoa

        conditional {
          if ($pessoa != null) {
            var.update $destino {
              value = $pessoa.user_id
            }
          }
        }
      }
    }

    // Preferencia "Na plataforma" do destinatario por assunto (change
    // configuracoes-seguranca-notificacoes, D2 e D3). Pedido novo (trabalho esperando a
    // decisao da pessoa) e recursos sem assunto (beneficio, cadastro, acesso) sempre chegam.
    var $assunto {
      value = null
    }

    conditional {
      if ($input.tipo != "pedido_novo") {
        conditional {
          if (($input.recurso == "ferias") || ($input.recurso == "ausencia")) {
            var.update $assunto {
              value = "ferias_ausencias"
            }
          }
        }

        conditional {
          if (($input.recurso == "correcao_ponto") || ($input.recurso == "registro_ponto")) {
            var.update $assunto {
              value = "ponto"
            }
          }
        }

        conditional {
          if (($input.recurso == "documento") || ($input.recurso == "pendencia_documento")) {
            var.update $assunto {
              value = "documentos"
            }
          }
        }

        conditional {
          if (($input.recurso == "avaliacao") || ($input.recurso == "formulario_meta")) {
            var.update $assunto {
              value = "avaliacoes_metas"
            }
          }
        }

        conditional {
          if ($input.recurso == "solicitacao_rh") {
            var.update $assunto {
              value = "solicitacoes"
            }
          }
        }

        // Publicacoes (change notificacoes-de-publicacao, D6).
        conditional {
          if ($input.recurso == "treinamento") {
            var.update $assunto {
              value = "treinamentos"
            }
          }
        }

        conditional {
          if (($input.recurso == "pesquisa_clima") || ($input.recurso == "humor")) {
            var.update $assunto {
              value = "pesquisas"
            }
          }
        }
      }
    }

    var $plataforma_ligada {
      value = true
    }

    conditional {
      if (($destino != null) && ($assunto != null)) {
        db.query preferencia_aviso {
          where = $db.preferencia_aviso.user_id == $destino && $db.preferencia_aviso.assunto == $assunto
          return = {type: "single"}
        } as $preferencia_aviso

        conditional {
          if (($preferencia_aviso != null) && ($preferencia_aviso.plataforma != true)) {
            var.update $plataforma_ligada {
              value = false
            }
          }
        }
      }
    }

    var $criada {
      value = false
    }

    conditional {
      if ($destino != null && $destino != $input.autor_user_id && $plataforma_ligada) {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $destino
            tipo                : $input.tipo
            titulo              : $input.titulo
            mensagem            : $input.mensagem
            recurso             : $input.recurso
            registro_id         : $input.registro_id
          }
        } as $notificacao

        var.update $criada {
          value = true
        }
      }
    }
  }

  response = $criada

  tags = ["conectahr"]
  guid = "conectahr-notificar-0001"
}
