// RH/ADMIN aciona a varredura de pendencias atrasadas (item 4.7).
// "Atrasada" = mais velha que prazo_dias, informado pelo proprio RH a
// cada chamada (o prazo e configuravel por execucao, nao um numero fixo
// do sistema). Sem Background Tasks neste plano Xano — acionamento
// manual reproduz o mesmo padrao ja usado em desligamento/documentos.
// Escalonamento = grava um evento em auditoria (idempotente por
// registro: nao duplica se ja escalonado antes) e retorna a lista para
// que RH/ADMIN vejam e ajam — nao ha canal de notificacao push/e-mail
// dedicado ainda (depende da central de notificacoes internas, item
// 5.11, e do outbox de e-mail, item 5.5, ainda nao implementados).
query "pendencias_atrasadas/escalonar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int prazo_dias filters=min:1
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh

    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }

    precondition ($perfil_rh == "RH" || $perfil_rh == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem escalonar pendencias atrasadas."
    }

    // now nao pode ser combinado com um acesso inline a campo/input na
    // mesma expressao aritmetica (ver conectahr-xano-platform-quirks,
    // achado 13) — pre-extrai prazo_dias antes de usar.
    var $prazo_dias_extraido {
      value = $input.prazo_dias
    }

    var $agora_escalonamento {
      value = now
    }

    var $limite_timestamp {
      value = ($agora_escalonamento - ($prazo_dias_extraido * 86400000))
    }

    var $escalonamentos_novos {
      value = []
    }

    var $ja_escalonados_antes {
      value = []
    }

    // Ferias pendentes.
    db.query ferias {
      where = $db.ferias.status == "Pendente" && $db.ferias.data_solicitacao <= $limite_timestamp
      return = {type: "list"}
    } as $ferias_atrasadas

    foreach ($ferias_atrasadas) {
      each as $item_ferias {
        db.query auditoria {
          where = $db.auditoria.acao == "escalonar_pendencia" && $db.auditoria.recurso == "ferias" && $db.auditoria.registro_id == $item_ferias.id
          return = {type: "single"}
        } as $ja_escalonado_ferias

        var $data_solicitacao_ferias_extraida {
          value = $item_ferias.data_solicitacao
        }

        var $agora_ferias_atrasada {
          value = now
        }

        var $dias_atraso_ferias {
          value = ((($agora_ferias_atrasada - $data_solicitacao_ferias_extraida) / 86400000)|to_int)
        }

        conditional {
          if ($ja_escalonado_ferias == null) {
            db.add auditoria {
              data = {
                user_id       : $usuario_rh.id
                acao          : "escalonar_pendencia"
                recurso       : "ferias"
                registro_id   : $item_ferias.id
                justificativa : "Solicitacao de ferias pendente ha " ~ ($dias_atraso_ferias|to_text) ~ " dias (prazo: " ~ ($input.prazo_dias|to_text) ~ "). Escalonado ao nivel superior (ADMIN)."
                resultado     : "sucesso"
              }
            } as $evento_escalonamento_ferias

            var.update $escalonamentos_novos {
              value = $escalonamentos_novos|push:{recurso: "ferias", registro_id: $item_ferias.id, dias_atraso: $dias_atraso_ferias}
            }
          }
        }

        conditional {
          if ($ja_escalonado_ferias != null) {
            var.update $ja_escalonados_antes {
              value = $ja_escalonados_antes|push:{recurso: "ferias", registro_id: $item_ferias.id, dias_atraso: $dias_atraso_ferias}
            }
          }
        }
      }
    }

    // Ausencias pendentes.
    db.query ausencia {
      where = $db.ausencia.status == "Pendente" && $db.ausencia.created_at <= $limite_timestamp
      return = {type: "list"}
    } as $ausencias_atrasadas

    foreach ($ausencias_atrasadas) {
      each as $item_ausencia {
        db.query auditoria {
          where = $db.auditoria.acao == "escalonar_pendencia" && $db.auditoria.recurso == "ausencia" && $db.auditoria.registro_id == $item_ausencia.id
          return = {type: "single"}
        } as $ja_escalonado_ausencia

        var $created_at_ausencia_extraido {
          value = $item_ausencia.created_at
        }

        var $agora_ausencia_atrasada {
          value = now
        }

        var $dias_atraso_ausencia {
          value = ((($agora_ausencia_atrasada - $created_at_ausencia_extraido) / 86400000)|to_int)
        }

        conditional {
          if ($ja_escalonado_ausencia == null) {
            db.add auditoria {
              data = {
                user_id       : $usuario_rh.id
                acao          : "escalonar_pendencia"
                recurso       : "ausencia"
                registro_id   : $item_ausencia.id
                justificativa : "Ausencia pendente ha " ~ ($dias_atraso_ausencia|to_text) ~ " dias (prazo: " ~ ($input.prazo_dias|to_text) ~ "). Escalonado ao nivel superior (ADMIN)."
                resultado     : "sucesso"
              }
            } as $evento_escalonamento_ausencia

            var.update $escalonamentos_novos {
              value = $escalonamentos_novos|push:{recurso: "ausencia", registro_id: $item_ausencia.id, dias_atraso: $dias_atraso_ausencia}
            }
          }
        }

        conditional {
          if ($ja_escalonado_ausencia != null) {
            var.update $ja_escalonados_antes {
              value = $ja_escalonados_antes|push:{recurso: "ausencia", registro_id: $item_ausencia.id, dias_atraso: $dias_atraso_ausencia}
            }
          }
        }
      }
    }

    // Solicitacoes de desligamento pendentes ou em analise.
    db.query solicitacao_desligamento {
      where = ($db.solicitacao_desligamento.status == "pendente" || $db.solicitacao_desligamento.status == "em_analise") && $db.solicitacao_desligamento.created_at <= $limite_timestamp
      return = {type: "list"}
    } as $desligamentos_atrasados

    foreach ($desligamentos_atrasados) {
      each as $item_desligamento {
        db.query auditoria {
          where = $db.auditoria.acao == "escalonar_pendencia" && $db.auditoria.recurso == "solicitacao_desligamento" && $db.auditoria.registro_id == $item_desligamento.id
          return = {type: "single"}
        } as $ja_escalonado_desligamento

        var $created_at_desligamento_extraido {
          value = $item_desligamento.created_at
        }

        var $agora_desligamento_atrasado {
          value = now
        }

        var $dias_atraso_desligamento {
          value = ((($agora_desligamento_atrasado - $created_at_desligamento_extraido) / 86400000)|to_int)
        }

        conditional {
          if ($ja_escalonado_desligamento == null) {
            db.add auditoria {
              data = {
                user_id       : $usuario_rh.id
                acao          : "escalonar_pendencia"
                recurso       : "solicitacao_desligamento"
                registro_id   : $item_desligamento.id
                justificativa : "Solicitacao de desligamento pendente ha " ~ ($dias_atraso_desligamento|to_text) ~ " dias (prazo: " ~ ($input.prazo_dias|to_text) ~ "). Escalonado ao nivel superior (ADMIN)."
                resultado     : "sucesso"
              }
            } as $evento_escalonamento_desligamento

            var.update $escalonamentos_novos {
              value = $escalonamentos_novos|push:{recurso: "solicitacao_desligamento", registro_id: $item_desligamento.id, dias_atraso: $dias_atraso_desligamento}
            }
          }
        }

        conditional {
          if ($ja_escalonado_desligamento != null) {
            var.update $ja_escalonados_antes {
              value = $ja_escalonados_antes|push:{recurso: "solicitacao_desligamento", registro_id: $item_desligamento.id, dias_atraso: $dias_atraso_desligamento}
            }
          }
        }
      }
    }

    // Solicitacoes gerais ao RH recebidas ou em analise.
    db.query solicitacao_rh {
      where = ($db.solicitacao_rh.status == "recebida" || $db.solicitacao_rh.status == "em_analise") && $db.solicitacao_rh.created_at <= $limite_timestamp
      return = {type: "list"}
    } as $solicitacoes_rh_atrasadas

    foreach ($solicitacoes_rh_atrasadas) {
      each as $item_solicitacao_rh {
        db.query auditoria {
          where = $db.auditoria.acao == "escalonar_pendencia" && $db.auditoria.recurso == "solicitacao_rh" && $db.auditoria.registro_id == $item_solicitacao_rh.id
          return = {type: "single"}
        } as $ja_escalonado_solicitacao_rh

        var $created_at_solicitacao_rh_extraido {
          value = $item_solicitacao_rh.created_at
        }

        var $agora_solicitacao_rh_atrasada {
          value = now
        }

        var $dias_atraso_solicitacao_rh {
          value = ((($agora_solicitacao_rh_atrasada - $created_at_solicitacao_rh_extraido) / 86400000)|to_int)
        }

        conditional {
          if ($ja_escalonado_solicitacao_rh == null) {
            db.add auditoria {
              data = {
                user_id       : $usuario_rh.id
                acao          : "escalonar_pendencia"
                recurso       : "solicitacao_rh"
                registro_id   : $item_solicitacao_rh.id
                justificativa : "Solicitacao ao RH pendente ha " ~ ($dias_atraso_solicitacao_rh|to_text) ~ " dias (prazo: " ~ ($input.prazo_dias|to_text) ~ "). Escalonado ao nivel superior (ADMIN)."
                resultado     : "sucesso"
              }
            } as $evento_escalonamento_solicitacao_rh

            var.update $escalonamentos_novos {
              value = $escalonamentos_novos|push:{recurso: "solicitacao_rh", registro_id: $item_solicitacao_rh.id, dias_atraso: $dias_atraso_solicitacao_rh}
            }
          }
        }

        conditional {
          if ($ja_escalonado_solicitacao_rh != null) {
            var.update $ja_escalonados_antes {
              value = $ja_escalonados_antes|push:{recurso: "solicitacao_rh", registro_id: $item_solicitacao_rh.id, dias_atraso: $dias_atraso_solicitacao_rh}
            }
          }
        }
      }
    }

    // Correcoes de ponto pendentes.
    db.query correcao_ponto {
      where = $db.correcao_ponto.status == "pendente" && $db.correcao_ponto.created_at <= $limite_timestamp
      return = {type: "list"}
    } as $correcoes_atrasadas

    foreach ($correcoes_atrasadas) {
      each as $item_correcao {
        db.query auditoria {
          where = $db.auditoria.acao == "escalonar_pendencia" && $db.auditoria.recurso == "correcao_ponto" && $db.auditoria.registro_id == $item_correcao.id
          return = {type: "single"}
        } as $ja_escalonado_correcao

        var $created_at_correcao_extraido {
          value = $item_correcao.created_at
        }

        var $agora_correcao_atrasada {
          value = now
        }

        var $dias_atraso_correcao {
          value = ((($agora_correcao_atrasada - $created_at_correcao_extraido) / 86400000)|to_int)
        }

        conditional {
          if ($ja_escalonado_correcao == null) {
            db.add auditoria {
              data = {
                user_id       : $usuario_rh.id
                acao          : "escalonar_pendencia"
                recurso       : "correcao_ponto"
                registro_id   : $item_correcao.id
                justificativa : "Correcao de ponto pendente ha " ~ ($dias_atraso_correcao|to_text) ~ " dias (prazo: " ~ ($input.prazo_dias|to_text) ~ "). Escalonado ao nivel superior (ADMIN)."
                resultado     : "sucesso"
              }
            } as $evento_escalonamento_correcao

            var.update $escalonamentos_novos {
              value = $escalonamentos_novos|push:{recurso: "correcao_ponto", registro_id: $item_correcao.id, dias_atraso: $dias_atraso_correcao}
            }
          }
        }

        conditional {
          if ($ja_escalonado_correcao != null) {
            var.update $ja_escalonados_antes {
              value = $ja_escalonados_antes|push:{recurso: "correcao_ponto", registro_id: $item_correcao.id, dias_atraso: $dias_atraso_correcao}
            }
          }
        }
      }
    }

    var $total_escalonados_agora {
      value = ($escalonamentos_novos|count)
    }

    var $total_ja_escalonados {
      value = ($ja_escalonados_antes|count)
    }
  }

  response = {
    sucesso              : true
    prazo_dias_usado      : $input.prazo_dias
    total_escalonados_agora: $total_escalonados_agora
    total_ja_escalonados     : $total_ja_escalonados
    escalonamentos_novos       : $escalonamentos_novos
    ja_escalonados_antes          : $ja_escalonados_antes
  }

  guid = "conectahr-pendencias-atrasadas-escalonar-post-0001"
}
