// Altera os dados de um beneficio do catalogo (tarefa 85): nome, tipo, operadora e descricao.
// Vale para todos que tem o beneficio, e cada um recebe o aviso no sino. Somente RH ou Admin.
query "beneficios/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text nome filters=trim|min:2|max:100
    text tipo filters=trim
    text? operadora? filters=trim|max:100
    text? descricao? filters=trim|max:2000
    json? links?
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.get beneficio {
      field_name = "id"
      field_value = $input.id
    } as $beneficio

    precondition ($beneficio != null) {
      error_type = "notfound"
      error = "Beneficio nao encontrado."
    }

    precondition (["vale_refeicao", "vale_alimentacao", "vale_transporte", "plano_saude", "plano_odontologico", "seguro_vida", "auxilio_home_office", "auxilio_creche", "outro"]|contains:$input.tipo) {
      error_type = "inputerror"
      error = "Tipo de beneficio invalido."
    }

    db.query beneficio {
      where = $db.beneficio.nome == $input.nome && $db.beneficio.id != $beneficio.id
      return = {type: "single"}
    } as $mesmo_nome

    precondition ($mesmo_nome == null) {
      error_type = "inputerror"
      error = "Ja existe um beneficio com este nome."
    }

    // Links da apresentacao (change apresentacao-de-beneficios, D3): ate 10, titulo de 2 a 80 e endereco https.
    // Sem `links` no pedido, os atuais continuam.
    var $links_final {
      value = ($input.links != null ? [] : $beneficio.links)
    }

    var $link_invalido {
      value = null
    }

    conditional {
      if ($input.links != null) {
        precondition (($input.links|count) <= 10) {
          error_type = "inputerror"
          error = "Cadastre no maximo 10 links por beneficio."
        }

        foreach ($input.links) {
          each as $link_item {
            var $link_titulo {
              value = (($link_item|get:"titulo") != null ? (($link_item|get:"titulo")|to_text|trim) : "")
            }

            var $link_url {
              value = (($link_item|get:"url") != null ? (($link_item|get:"url")|to_text|trim) : "")
            }

            conditional {
              if (($link_titulo|strlen) < 2 || ($link_titulo|strlen) > 80 || ($link_url|starts_with:"https://") == false || ($link_url|strlen) > 500 || ($link_url|strlen) < 12) {
                var.update $link_invalido {
                  value = ($link_titulo != "" ? $link_titulo : $link_url)
                }
              }

              else {
                var.update $links_final {
                  value = $links_final|push:{titulo: $link_titulo, url: $link_url}
                }
              }
            }
          }
        }
      }
    }

    precondition ($link_invalido == null) {
      error_type = "inputerror"
      error = "Link invalido: cada link precisa de um titulo (2 a 80 caracteres) e de um endereco que comece com https://."
    }

    db.edit beneficio {
      field_name = "id"
      field_value = $beneficio.id
      data = {nome: $input.nome, tipo: $input.tipo, operadora: $input.operadora, descricao: $input.descricao, links: $links_final, updated_at: "now"}
    } as $beneficio_atualizado

    db.query colaborador_beneficio {
      where = $db.colaborador_beneficio.beneficio_id == $beneficio.id && $db.colaborador_beneficio.ativo == true
      return = {type: "list"}
    } as $vinculos_do_beneficio

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $avisados {
      value = 0
    }

    foreach ($vinculos_do_beneficio) {
      each as $vinculo_aviso {
        conditional {
          if ($vinculo_aviso.data_fim == null || $vinculo_aviso.data_fim >= $hoje) {
            db.get colaborador {
              field_name = "id"
              field_value = $vinculo_aviso.colaborador_id
            } as $pessoa_aviso

            conditional {
              if ($pessoa_aviso != null && $pessoa_aviso.user_id != null) {
                db.add notificacao_interna {
                  data = {
                    destinatario_user_id: $pessoa_aviso.user_id
                    tipo                : "beneficio_atualizado"
                    titulo              : "Seu beneficio " ~ $input.nome ~ " foi atualizado"
                    mensagem            : "O RH atualizou as informacoes do beneficio " ~ $input.nome ~ ". Veja em Beneficios."
                    recurso             : "beneficio"
                    registro_id         : $vinculo_aviso.beneficio_id
                  }
                } as $aviso_beneficio
              }
            }

            var.update $avisados {
              value = $avisados + 1
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id     : $usuario_autenticado.id
        acao        : "editar_beneficio"
        recurso     : "beneficio"
        registro_id : $beneficio.id
        valor_anterior: $beneficio.nome
        valor_novo  : $input.nome
        resultado   : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    beneficio: $beneficio_atualizado
    avisados : $avisados
  }

  guid = "conectahr-beneficios-id-patch-0001"
}
