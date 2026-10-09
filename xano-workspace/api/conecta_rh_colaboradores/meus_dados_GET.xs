// Exportacao dos dados pessoais do proprio colaborador (LGPD, art. 18, II e V).
// So devolve os dados de quem esta autenticado. `formato=json` (padrao) traz tudo;
// `formato=csv` traz um resumo (categoria, id, tipo, status, data) de cada registro.
//
// Fora da exportacao, de proposito:
//  - respostas de pesquisa de clima (sao anonimas, nao ha vinculo com a pessoa);
//  - dados de terceiros (avaliacoes recebidas trazem so os metadados, sem a nota
//    nem o comentario de quem avaliou);
//  - senha, codigos de acesso, comprovantes, imagens e links de arquivo.
// Cada exportacao grava `exportar_meus_dados` na auditoria.
query meus_dados verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text? formato? filters=trim|lower
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

    var $formato_final {
      value = ($input.formato == null || $input.formato == "" ? "json" : $input.formato)
    }

    precondition ($formato_final == "json" || $formato_final == "csv") {
      error_type = "inputerror"
      error = "Formato invalido. Use json ou csv."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_proprio

    // Sem colaborador vinculado (ex.: conta de Admin) as listas de colaborador ficam vazias.
    var $colab_id {
      value = ($colaborador_proprio != null ? $colaborador_proprio.id : 0)
    }

    db.query historico_profissional {
      where = $db.historico_profissional.colaborador_id == $colab_id
      return = {type: "list"}
    } as $historico

    db.query documento {
      where = $db.documento.colaborador_id == $colab_id
      return = {type: "list"}
      output = ["id", "created_at", "tipo", "nome_documento", "estado_de_emissao", "data_emissao", "data_validade", "retencao_ate", "status", "estado_verificacao", "ativo"]
    } as $documentos

    db.query ferias {
      where = $db.ferias.colaborador_id == $colab_id
      return = {type: "list"}
    } as $ferias

    db.query ausencia {
      where = $db.ausencia.colaborador_id == $colab_id
      return = {type: "list"}
      output = ["id", "created_at", "tipo", "data_inicio", "data_fim", "motivo_tipo", "status", "observacao"]
    } as $ausencias

    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colab_id
      return = {type: "list"}
    } as $ponto

    db.query banco_horas_lancamento {
      where = $db.banco_horas_lancamento.colaborador_id == $colab_id
      return = {type: "list"}
    } as $banco_de_horas

    db.query avaliacao {
      where = $db.avaliacao.user_id == $usuario_autenticado.id
      return = {type: "list"}
    } as $avaliacoes_que_eu_fiz

    db.query avaliacao {
      where = $db.avaliacao.colaborador_id == $colab_id && $db.avaliacao.user_id != $usuario_autenticado.id
      return = {type: "list"}
      output = ["id", "ciclo_avaliacao_id", "relacao_avaliador", "periodo_incio", "periodo_fim", "status", "data_avaliacao"]
    } as $avaliacoes_recebidas

    db.query meta_avaliacao {
      where = $db.meta_avaliacao.colaborador_id == $colab_id
      return = {type: "list"}
    } as $metas

    db.query pdi {
      where = $db.pdi.colaborador_id == $colab_id
      return = {type: "list"}
    } as $pdi

    db.query solicitacao_rh {
      where = $db.solicitacao_rh.colaborador_id == $colab_id
      return = {type: "list"}
    } as $solicitacoes

    db.query notificacao_interna {
      where = $db.notificacao_interna.destinatario_user_id == $usuario_autenticado.id
      return = {type: "list"}
    } as $notificacoes

    db.query sessao {
      where = $db.sessao.user_id == $usuario_autenticado.id
      return = {type: "list"}
      output = ["id", "created_at", "expira_em", "revogada_em", "dispositivo", "endereco_ip", "ativa"]
    } as $sessoes

    var $usuario {
      value = {
        id           : $usuario_autenticado.id
        nome         : $usuario_autenticado.nome
        email        : $usuario_autenticado.email
        perfil       : $usuario_autenticado.perfil
        ativo        : $usuario_autenticado.ativo
        ultimo_acesso: $usuario_autenticado.ultimo_acesso
      }
    }

    var $csv {
      value = ""
    }

    var $quebra_linha {
      value = "\n"
    }

    conditional {
      if ($formato_final == "csv") {
        var.update $csv {
          value = ("categoria,id,tipo,status,data" ~ $quebra_linha)
        }

        foreach ($historico) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "historico," ~ ($linha.id|to_text) ~ "," ~ ($linha.tipo_alteracao != null ? ($linha.tipo_alteracao|to_text|replace:",":" ") : "") ~ "," ~ ($linha.tipo_contrato != null ? ($linha.tipo_contrato|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_inicio != null ? ($linha.data_inicio|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($documentos) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "documentos," ~ ($linha.id|to_text) ~ "," ~ ($linha.tipo != null ? ($linha.tipo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_validade != null ? ($linha.data_validade|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($ferias) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "ferias," ~ ($linha.id|to_text) ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_inicio != null ? ($linha.data_inicio|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($ausencias) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "ausencias," ~ ($linha.id|to_text) ~ "," ~ ($linha.tipo != null ? ($linha.tipo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_inicio != null ? ($linha.data_inicio|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($ponto) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "ponto," ~ ($linha.id|to_text) ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data != null ? ($linha.data|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($banco_de_horas) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "banco_de_horas," ~ ($linha.id|to_text) ~ "," ~ ($linha.tipo != null ? ($linha.tipo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.origem != null ? ($linha.origem|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_lancamento != null ? ($linha.data_lancamento|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($avaliacoes_que_eu_fiz) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "avaliacoes_que_eu_fiz," ~ ($linha.id|to_text) ~ "," ~ ($linha.relacao_avaliador != null ? ($linha.relacao_avaliador|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_avaliacao != null ? ($linha.data_avaliacao|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($avaliacoes_recebidas) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "avaliacoes_recebidas," ~ ($linha.id|to_text) ~ "," ~ ($linha.relacao_avaliador != null ? ($linha.relacao_avaliador|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_avaliacao != null ? ($linha.data_avaliacao|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($metas) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "metas," ~ ($linha.id|to_text) ~ "," ~ ($linha.titulo != null ? ($linha.titulo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_prazo != null ? ($linha.data_prazo|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($pdi) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "pdi," ~ ($linha.id|to_text) ~ "," ~ ($linha.titulo != null ? ($linha.titulo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_prazo != null ? ($linha.data_prazo|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($solicitacoes) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "solicitacoes," ~ ($linha.id|to_text) ~ "," ~ ($linha.tipo != null ? ($linha.tipo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.status != null ? ($linha.status|to_text|replace:",":" ") : "") ~ "," ~ ($linha.data_decisao != null ? ($linha.data_decisao|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($notificacoes) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "notificacoes," ~ ($linha.id|to_text) ~ "," ~ ($linha.tipo != null ? ($linha.tipo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.tipo != null ? ($linha.tipo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.created_at != null ? ($linha.created_at|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

        foreach ($sessoes) {
          each as $linha {
            var.update $csv {
              value = ($csv ~ "sessoes," ~ ($linha.id|to_text) ~ "," ~ ($linha.dispositivo != null ? ($linha.dispositivo|to_text|replace:",":" ") : "") ~ "," ~ ($linha.ativa != null ? ($linha.ativa|to_text|replace:",":" ") : "") ~ "," ~ ($linha.created_at != null ? ($linha.created_at|to_text|replace:",":" ") : "") ~ $quebra_linha)
            }
          }
        }

      }
    }

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "exportar_meus_dados"
        recurso      : "user"
        registro_id  : $usuario_autenticado.id
        justificativa: ("formato=" ~ $formato_final)
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    formato : $formato_final
    usuario : $usuario
    colaborador: $colaborador_proprio
      historico: $historico
      documentos: $documentos
      ferias: $ferias
      ausencias: $ausencias
      ponto: $ponto
      banco_de_horas: $banco_de_horas
      avaliacoes_que_eu_fiz: $avaliacoes_que_eu_fiz
      avaliacoes_recebidas: $avaliacoes_recebidas
      metas: $metas
      pdi: $pdi
      solicitacoes: $solicitacoes
      notificacoes: $notificacoes
      sessoes: $sessoes
    csv     : $csv
  }

  guid = "conectahr-meus-dados-get-0001"
}
