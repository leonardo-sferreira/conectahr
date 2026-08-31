// Processa vencimentos de documentos aprovados: transiciona para
// `vencido` os que ja passaram da data_validade e envia alertas por
// e-mail aos que se aproximam (30, 15 ou 7 dias, ou no dia do
// vencimento). Acionamento manual pelo RH/ADMIN em vez de rotina
// automatica diaria: o plano Xano deste workspace nao inclui
// Background Tasks e o upgrade foi recusado (ver design.md, secao
// "Documentos vencidos" e a decisao equivalente em "Desligamento").
// Idempotente por documento: `ultimo_alerta_dias` guarda o menor
// limiar (30/15/7/0) ja alertado, entao rodar este endpoint varias
// vezes no mesmo dia nao reenvia o mesmo alerta.
query "documentos/processar_vencimentos" verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuario autenticado.
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem processar vencimentos de documentos."
    }

    // Documentos aprovados com validade definida sao os unicos candidatos.
    db.query documento {
      where = $db.documento.status == "aprovado" && $db.documento.data_validade != null
      return = {type: "list"}
    } as $documentos_aprovados

    var $total_vencidos {
      value = 0
    }

    var $total_alertas {
      value = 0
    }

    foreach ($documentos_aprovados) {
      each as $documento_item {
        // Dias restantes ate a validade (zero ou negativo = ja venceu).
        // data_validade e um campo "date" (string) — precisa de
        // |to_timestamp antes de aritmetica, com o valor pre-extraido
        // antes de combinar com now (ver conectahr-xano-platform-quirks,
        // achado 13).
        var $data_validade_ts {
          value = ($documento_item.data_validade|to_timestamp)
        }

        var $agora_vencimento {
          value = now
        }

        var $dias_restantes {
          value = ((($data_validade_ts - $agora_vencimento) / 86400000)|to_int)
        }

        var $venceu {
          value = ($dias_restantes <= 0)
        }

        // Limiar de proximidade (30/15/7 dias) quando ainda nao venceu.
        var $limiar_atingido {
          value = null
        }

        conditional {
          if ($dias_restantes <= 30 && $dias_restantes > 15) {
            var.update $limiar_atingido {
              value = 30
            }
          }
        }

        conditional {
          if ($dias_restantes <= 15 && $dias_restantes > 7) {
            var.update $limiar_atingido {
              value = 15
            }
          }
        }

        conditional {
          if ($dias_restantes <= 7 && $dias_restantes > 0) {
            var.update $limiar_atingido {
              value = 7
            }
          }
        }

        // Transiciona o status quando a validade ja passou. O
        // vencimento nunca altera o status do colaborador.
        conditional {
          if ($venceu) {
            db.edit documento {
              field_name = "id"
              field_value = $documento_item.id
              data = {status: "vencido", updated_at: "now"}
            } as $documento_vencido

            var.update $total_vencidos {
              value = $total_vencidos + 1
            }
          }
        }

        // Limiar efetivo para fins de alerta: 0 no dia do vencimento,
        // senao o limiar de proximidade identificado acima (ou nenhum).
        var $limiar_alerta {
          value = ($venceu ? 0 : $limiar_atingido)
        }

        // So alerta quando ha um limiar novo, ainda nao coberto pelo
        // ultimo alerta enviado para este documento.
        var $deve_alertar {
          value = ($limiar_alerta != null && ($documento_item.ultimo_alerta_dias == null || $documento_item.ultimo_alerta_dias > $limiar_alerta))
        }

        conditional {
          if ($deve_alertar) {
            db.get colaborador {
              field_name = "id"
              field_value = $documento_item.colaborador_id
            } as $colaborador_documento

            conditional {
              if ($colaborador_documento != null) {
                // Alerta de vencimento vira notificacao assincrona via
                // outbox (item 5.5), com retentativa, em vez de envio
                // sincrono direto — mais adequado para um alerta em
                // lote que nao tem ninguem esperando a resposta na hora.
                var $assunto_alerta {
                  value = ($venceu ? ("Documento venceu hoje: " ~ $documento_item.nome_documento) : ("Documento vence em " ~ ($limiar_alerta|to_text) ~ " dias: " ~ $documento_item.nome_documento))
                }

                var $corpo_alerta {
                  value = ($venceu ? ("O documento " ~ $documento_item.nome_documento ~ " venceu hoje. Envie uma substituicao assim que possivel.") : ("O documento " ~ $documento_item.nome_documento ~ " vence em " ~ ($limiar_alerta|to_text) ~ " dias. Envie uma substituicao antes do vencimento."))
                }

                db.add email_outbox {
                  data = {
                    destinatario_email: $colaborador_documento.email_pessoal
                    destinatario_nome : $colaborador_documento.nome
                    assunto           : $assunto_alerta
                    corpo             : $corpo_alerta
                    chave_idempotencia: ("documento_vencendo_" ~ ($documento_item.id|to_text) ~ "_" ~ ($limiar_alerta|to_text))
                  }
                } as $outbox_alerta_criado

                conditional {
                  if ($colaborador_documento.user_id != null) {
                    db.add notificacao_interna {
                      data = {
                        destinatario_user_id: $colaborador_documento.user_id
                        tipo                : "documento_vencendo"
                        titulo              : $assunto_alerta
                        mensagem            : $corpo_alerta
                        recurso             : "documento"
                        registro_id         : $documento_item.id
                      }
                    } as $notificacao_alerta_criada
                  }
                }

                db.edit documento {
                  field_name = "id"
                  field_value = $documento_item.id
                  data = {ultimo_alerta_dias: $limiar_alerta}
                } as $documento_alertado

                var.update $total_alertas {
                  value = $total_alertas + 1
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso       : true
    mensagem      : "Processamento de vencimentos concluido."
    total_vencidos: $total_vencidos
    total_alertas : $total_alertas
  }

  guid = "conectahr-documentos-processar-vencimentos-0001"
}
