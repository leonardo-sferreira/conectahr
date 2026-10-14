// Gera as pendencias de documento obrigatorio (pedido do usuario em 13/10/2026): para cada regra ativa e obrigatoria de
// documento_obrigatorio_regra que se aplica a pessoa (contrato, cargo, departamento e faixa de idade), cria uma
// pendencia_documento com prazo = hoje + prazo_dias_para_envio (10 sem prazo na regra). Pula o documento que ja esta
// aprovado ou em analise (RG e CIN valem um pelo outro) e o que ja tem pendencia aberta: rodar de novo nao duplica.
// Uso: colaboradores POST (a pessoa admitida) e a mao pela CLI, para todos os nao desligados (colaborador_id vazio),
// com `excluir_email` para deixar alguem de fora. Avisa a pessoa (uma notificacao) e audita por pessoa. A resposta traz
// so ids e contagens, sem dado pessoal. Com `simular`, so conta (nao grava pendencia, aviso nem auditoria).
function "ConectaHR/gerar_pendencias_obrigatorias" {
  input {
    int? colaborador_id?
    text? excluir_email? filters=trim|lower
    int? autor_user_id?
    // true: so conta o que seria criado, sem gravar nada.
    bool? simular?
  }

  stack {
    // Autor: quem pediu ou, sem ele, o primeiro ADMIN ativo (ou o primeiro RH).
    var $autor_id {
      value = $input.autor_user_id
    }

    conditional {
      if ($autor_id == null) {
        db.query user {
          return = {type: "list"}
        } as $usuarios

        var $autor_rh_id {
          value = null
        }

        foreach ($usuarios) {
          each as $u {
            conditional {
              if (($autor_id == null) && (($u.perfil|trim|to_upper) == "ADMIN") && $u.ativo) {
                var.update $autor_id {
                  value = $u.id
                }
              }

              elseif (($autor_rh_id == null) && (($u.perfil|trim|to_upper) == "RH") && $u.ativo) {
                var.update $autor_rh_id {
                  value = $u.id
                }
              }
            }
          }
        }

        conditional {
          if ($autor_id == null) {
            var.update $autor_id {
              value = $autor_rh_id
            }
          }
        }
      }
    }

    precondition ($autor_id != null) {
      error_type = "standard"
      error = "Nao ha usuario ADMIN ou RH ativo para assinar as pendencias."
    }

    db.query documento_obrigatorio_regra {
      where = $db.documento_obrigatorio_regra.ativo == true && $db.documento_obrigatorio_regra.obrigatorio == true
      return = {type: "list"}
    } as $regras

    // Pessoas: a indicada ou todas.
    var $pessoas {
      value = []
    }

    conditional {
      if ($input.colaborador_id != null) {
        db.get colaborador {
          field_name = "id"
          field_value = $input.colaborador_id
        } as $uma_pessoa

        precondition ($uma_pessoa != null) {
          error_type = "notfound"
          error = "Colaborador nao encontrado."
        }

        var.update $pessoas {
          value = []|push:$uma_pessoa
        }
      }

      else {
        db.query colaborador {
          return = {type: "list"}
        } as $todas_pessoas

        var.update $pessoas {
          value = $todas_pessoas
        }
      }
    }

    var $hoje_ts {
      value = now
    }

    var $resultado {
      value = []
    }

    var $total_criadas {
      value = 0
    }

    var $excluidos {
      value = 0
    }

    foreach ($pessoas) {
      each as $p {
        // E-mail da conta (para a exclusao), quando ha conta.
        var $email_conta {
          value = ""
        }

        conditional {
          if ($p.user_id != null) {
            db.get user {
              field_name = "id"
              field_value = $p.user_id
            } as $conta_p

            conditional {
              if ($conta_p != null) {
                var.update $email_conta {
                  value = ($conta_p.email|to_lower)
                }
              }
            }
          }
        }

        var $excluir {
          value = (($input.excluir_email != null) && ($input.excluir_email != "") && ((($p.email_pessoal|to_lower) == $input.excluir_email) || ($email_conta == $input.excluir_email)))
        }

        var $desligado {
          value = (($p.status|trim|to_upper) == "DESLIGADO")
        }

        conditional {
          if ($excluir) {
            var.update $excluidos {
              value = $excluidos + 1
            }
          }
        }

        conditional {
          if (($excluir == false) && ($desligado == false)) {
            // Idade em anos inteiros (sem data de nascimento, regras com faixa de idade nao se aplicam).
            var $idade {
              value = null
            }

            conditional {
              if ($p.data_nascimento != null) {
                var.update $idade {
                  value = (((($hoje_ts - ($p.data_nascimento|to_timestamp)) / 86400000) / 365)|to_int)
                }
              }
            }

            // Documentos e pendencias que a pessoa ja tem, como texto (",rg,cnh,"): contains em lista nao funciona.
            db.query documento {
              where = $db.documento.colaborador_id == $p.id
              return = {type: "list"}
            } as $docs_p

            var $tipos_com_documento {
              value = ","
            }

            foreach ($docs_p) {
              each as $dp {
                conditional {
                  if (($dp.status == "aprovado") || ($dp.status == "pendente_analise")) {
                    var.update $tipos_com_documento {
                      value = $tipos_com_documento ~ $dp.tipo ~ ","
                    }
                  }
                }
              }
            }

            db.query pendencia_documento {
              where = $db.pendencia_documento.colaborador_id == $p.id && $db.pendencia_documento.status == "pendente"
              return = {type: "list"}
            } as $pend_p

            var $tipos_com_pendencia {
              value = ","
            }

            foreach ($pend_p) {
              each as $pp {
                var.update $tipos_com_pendencia {
                  value = $tipos_com_pendencia ~ $pp.tipo_documento ~ ","
                }
              }
            }

            var $criadas_p {
              value = 0
            }

            foreach ($regras) {
              each as $r {
                var $aplica {
                  value = ((($r.tipo_contrato == null) || ($r.tipo_contrato == $p.tipo_contrato)) && (($r.cargo_id == null) || ($r.cargo_id == $p.cargo_id)) && (($r.departamento_id == null) || ($r.departamento_id == $p.departamento_id)) && (($r.idade_minima == null) || (($idade != null) && ($idade >= $r.idade_minima))) && (($r.idade_maxima == null) || (($idade != null) && ($idade <= $r.idade_maxima))))
                }

                var $tipo_r {
                  value = "," ~ $r.tipo_documento ~ ","
                }

                var $equivalente {
                  value = ($r.tipo_documento == "rg" ? ",cin," : ($r.tipo_documento == "cin" ? ",rg," : ",nenhum,"))
                }

                var $ja_tem {
                  value = (($tipos_com_documento|contains:$tipo_r) || ($tipos_com_documento|contains:$equivalente) || ($tipos_com_pendencia|contains:$tipo_r))
                }

                conditional {
                  if ($aplica && ($ja_tem == false)) {
                    var $prazo_dias {
                      value = ($r.prazo_dias_para_envio != null ? $r.prazo_dias_para_envio : 10)
                    }

                    conditional {
                      if ($input.simular != true) {
                    db.add pendencia_documento {
                      data = {
                        colaborador_id        : $p.id
                        tipo_documento        : $r.tipo_documento
                        prazo                 : ($hoje_ts|add_secs_to_timestamp:($prazo_dias * 86400)|format_timestamp:"Y-m-d":"America/Sao_Paulo")
                        observacao            : "Documento obrigatorio para o seu contrato. Envie pela tela Documentos."
                        status                : "pendente"
                        solicitado_por_user_id: $autor_id
                        updated_at            : "now"
                      }
                    } as $nova_pendencia
                      }
                    }

                    // Marca o tipo para nao criar duas pendencias do mesmo documento nesta execucao.
                    var.update $tipos_com_pendencia {
                      value = $tipos_com_pendencia ~ $r.tipo_documento ~ ","
                    }

                    var.update $criadas_p {
                      value = $criadas_p + 1
                    }
                  }
                }
              }
            }

            conditional {
              if (($criadas_p > 0) && ($input.simular != true)) {
                conditional {
                  if ($p.user_id != null) {
                    db.add notificacao_interna {
                      data = {
                        destinatario_user_id: $p.user_id
                        tipo                : "documento_pedido"
                        titulo              : "Documentos para enviar"
                        mensagem            : "O RH pediu " ~ ($criadas_p|to_text) ~ " documento(s) obrigatorio(s) do seu contrato. Envie pela tela Documentos."
                        recurso             : "documento"
                        registro_id         : $p.id
                      }
                    } as $aviso_pendencias
                  }
                }

                db.add auditoria {
                  data = {
                    user_id    : $autor_id
                    acao       : "gerar_pendencias_obrigatorias"
                    recurso    : "colaborador"
                    registro_id: $p.id
                    valor_novo : "pendencias criadas=" ~ ($criadas_p|to_text)
                    resultado  : "sucesso"
                  }
                } as $evento_auditoria
              }
            }

            var.update $total_criadas {
              value = $total_criadas + $criadas_p
            }

            var.update $resultado {
              value = $resultado|push:{colaborador_id: $p.id, pendencias_criadas: $criadas_p}
            }
          }
        }
      }
    }
  }

  response = {
    simulacao    : ($input.simular == true)
    total_criadas: $total_criadas
    excluidos    : $excluidos
    por_pessoa   : $resultado
  }

  tags = ["conectahr"]
  guid = "conectahr-gerar-pendencias-obrigatorias-0001"
}
