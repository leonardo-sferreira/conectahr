// Aprova uma correcao de ponto: aplica o valor solicitado no marcador
// indicado, recalcula horas_trabalhadas quando os quatro marcadores do
// dia estiverem presentes, e marca o registro como Ajustado. O valor
// original ja fica preservado em `correcao_ponto.valor_original` desde
// a solicitacao. Responsavel autorizado: RH, ADMIN, ou o Gestor do
// departamento do colaborador.
query "correcoes_ponto/{id}/aprovar" verb=POST {
  api_group = "ConectaRH - Ponto"
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get correcao_ponto {
      field_name = "id"
      field_value = $input.id
    } as $correcao_atual

    precondition ($correcao_atual != null) {
      error_type = "notfound"
      error = "Solicitacao de correcao nao encontrada."
    }

    // Bloqueio de autoaprovacao: ninguem decide uma solicitacao em que e o
    // proprio colaborador, nem RH/ADMIN. A tentativa e auditada antes da recusa.
    db.get colaborador {
      field_name = "user_id"
      field_value = $auth.id
    } as $colaborador_do_decisor

    conditional {
      if ($colaborador_do_decisor != null && $colaborador_do_decisor.id == $correcao_atual.colaborador_id) {
        db.add auditoria {
          data = {
            user_id    : $auth.id
            acao       : "autoaprovacao_bloqueada"
            recurso    : "correcao_ponto"
            registro_id: $correcao_atual.id
            resultado  : "falha"
          }
        } as $evento_autoaprovacao

        precondition (false) {
          error_type = "accessdenied"
          error = "Voce nao pode decidir uma solicitacao propria."
        }
      }
    }

    precondition ($correcao_atual.status == "pendente") {
      error_type = "inputerror"
      error = "Somente solicitacoes pendentes podem ser aprovadas."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $correcao_atual.colaborador_id
    } as $colaborador_da_correcao

    precondition ($colaborador_da_correcao != null) {
      error_type = "notfound"
      error = "Colaborador relacionado a correcao nao encontrado."
    }

    // Verifica se o autenticado e o Gestor do departamento do colaborador.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $e_gestor_da_equipe {
      value = false
    }

    conditional {
      if ($perfil_autenticado == "GESTOR" && $colaborador_autenticado != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerenciado

        conditional {
          if ($departamento_gerenciado != null && $colaborador_da_correcao.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_da_equipe {
              value = true
            }
          }
        }
      }
    }

    // Substituto com delegacao vigente (design D6): existe uma delegacao ativa, dentro
    // do periodo, com escopo "correcao_ponto" ou "todas", cujo titular e o Gestor do departamento
    // do colaborador. A tentativa so vale para quem nao tem o escopo por outro caminho.
    var $titular_delegacao_id {
      value = null
    }

    var $escopo_ok {
      value = (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN") || $e_gestor_da_equipe)
    }

    conditional {
      if ($escopo_ok == false && $colaborador_da_correcao != null) {
        var $hoje_delegacao {
          value = now|format_timestamp:"Y-m-d":"UTC"
        }

        db.query delegacao_aprovacao {
          where = $db.delegacao_aprovacao.substituto_user_id == $usuario_autenticado.id && $db.delegacao_aprovacao.cancelada_em == null && $db.delegacao_aprovacao.data_inicio <= $hoje_delegacao && $db.delegacao_aprovacao.data_fim >= $hoje_delegacao && ($db.delegacao_aprovacao.escopo == "correcao_ponto" || $db.delegacao_aprovacao.escopo == "todas")
          return = {type: "list"}
        } as $delegacoes_vigentes

        foreach ($delegacoes_vigentes) {
          each as $delegacao_item {
            conditional {
              if ($titular_delegacao_id == null) {
                db.get colaborador {
                  field_name = "user_id"
                  field_value = $delegacao_item.titular_user_id
                } as $colaborador_titular

                conditional {
                  if ($colaborador_titular != null) {
                    db.query departamento {
                      where = $db.departamento.gestor_colaborador_id == $colaborador_titular.id && $db.departamento.id == $colaborador_da_correcao.departamento_id
                      return = {type: "single"}
                    } as $departamento_do_titular

                    conditional {
                      if ($departamento_do_titular != null) {
                        var.update $titular_delegacao_id {
                          value = $delegacao_item.titular_user_id
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    var $nota_delegacao {
      value = ($titular_delegacao_id != null ? ("decisao por delegacao do titular user_id=" ~ ($titular_delegacao_id|to_text)) : "")
    }

    precondition ($escopo_ok || $titular_delegacao_id != null) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para decidir esta correcao de ponto."
    }

    db.get registro_ponto {
      field_name = "id"
      field_value = $correcao_atual.registro_ponto_id
    } as $registro_alvo

    precondition ($registro_alvo != null) {
      error_type = "notfound"
      error = "Registro de ponto relacionado nao encontrado."
    }

    db.transaction {
      stack {
        // Aplica o valor solicitado no campo correto (sem campo dinamico em XanoScript).
        conditional {
          if ($correcao_atual.campo == "hora_entrada") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {hora_entrada: $correcao_atual.valor_solicitado, updated_at: "now"}
            } as $registro_editado_1
          }
        }

        conditional {
          if ($correcao_atual.campo == "inicio_intervalo") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {inicio_intervalo: $correcao_atual.valor_solicitado, updated_at: "now"}
            } as $registro_editado_2
          }
        }

        conditional {
          if ($correcao_atual.campo == "fim_intervalo") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {fim_intervalo: $correcao_atual.valor_solicitado, updated_at: "now"}
            } as $registro_editado_3
          }
        }

        conditional {
          if ($correcao_atual.campo == "hora_saida") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {hora_saida: $correcao_atual.valor_solicitado, updated_at: "now"}
            } as $registro_editado_4
          }
        }

        db.get registro_ponto {
          field_name = "id"
          field_value = $registro_alvo.id
        } as $registro_apos_correcao

        // Recalcula horas trabalhadas somente quando os quatro marcadores existem.
        var $todos_marcadores_presentes {
          value = ($registro_apos_correcao.hora_entrada != null && $registro_apos_correcao.inicio_intervalo != null && $registro_apos_correcao.fim_intervalo != null && $registro_apos_correcao.hora_saida != null)
        }

        conditional {
          if ($todos_marcadores_presentes) {
            var $duracao_bruta_ms {
              value = $registro_apos_correcao.hora_saida - $registro_apos_correcao.hora_entrada
            }

            var $duracao_intervalo_ms {
              value = $registro_apos_correcao.fim_intervalo - $registro_apos_correcao.inicio_intervalo
            }

            var $horas_trabalhadas_recalculadas {
              value = ($duracao_bruta_ms - $duracao_intervalo_ms) / 3600000
            }

            // Horas extras parametrizadas pela matriz regra_contrato (item 4.1).
            db.query regra_contrato {
              where = $db.regra_contrato.tipo_contrato == $colaborador_da_correcao.tipo_contrato && $db.regra_contrato.ativo == true
              return = {type: "single"}
            } as $regra_correcao

            var $horas_extras_recalculadas {
              value = 0
            }

            conditional {
              if ($regra_correcao != null && $regra_correcao.permite_hora_extra == true && $regra_correcao.horas_diarias != null && $horas_trabalhadas_recalculadas > $regra_correcao.horas_diarias) {
                var.update $horas_extras_recalculadas {
                  value = $horas_trabalhadas_recalculadas - $regra_correcao.horas_diarias
                }
              }
            }

            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_apos_correcao.id
              data = {
                horas_trabalhadas: $horas_trabalhadas_recalculadas
                horas_extras     : $horas_extras_recalculadas
                status            : "Ajustado"
                updated_at        : "now"
              }
            } as $registro_final_completo
          }
        }

        conditional {
          if ($todos_marcadores_presentes == false) {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_apos_correcao.id
              data = {status: "Ajustado", updated_at: "now"}
            } as $registro_final_incompleto
          }
        }

        db.edit correcao_ponto {
          field_name = "id"
          field_value = $correcao_atual.id
          data = {
            status                : "aprovada"
            decidido_por_user_id  : $usuario_autenticado.id
            data_decisao           : "now"
            updated_at              : "now"
          }
        } as $correcao_aprovada

        // Auditoria: aprovacao de correcao de ponto.
        db.add auditoria {
          data = {
            user_id       : $usuario_autenticado.id
            acao          : "aprovar_correcao_ponto"
            recurso       : "correcao_ponto"
            registro_id   : $correcao_atual.id
            justificativa : $nota_delegacao
            valor_anterior: ($correcao_atual.valor_original|to_text)
            valor_novo    : ($correcao_atual.valor_solicitado|to_text)
            resultado     : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Correcao de ponto aprovada com sucesso."
  }

  guid = "conectahr-correcoes-ponto-aprovar-post-0001"
}
