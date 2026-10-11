// Ajuste direto do ponto de outra pessoa (tarefa 81): o superior direto, o Gestor do
// departamento (para quem nao tem superior), o RH ou o Admin corrigem uma marcacao com
// motivo, e vale na hora. Ninguem ajusta o proprio ponto: o pedido da pessoa vai para o
// superior dela. Cria o registro do dia quando nao existe, aplica o horario, recalcula as
// horas, grava o historico como correcao aprovada, audita e avisa a pessoa.
query "folha_ponto/ajustar" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int colaborador_id
    date data
    text campo filters=trim
    timestamp valor_solicitado
    text motivo filters=trim|min:5|max:1000
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $ve_todos {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    precondition ($ve_todos || $colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    // Quem a pessoa pode ver (tarefa 81): RH e Admin, todos; os demais, a si mesmos, quem os
    // tem como superior direto e, de quem nao tem superior, o departamento que gerenciam.
    var $departamento_gerido_id {
      value = null
    }

    conditional {
      if ($colaborador_autenticado != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerido

        conditional {
          if ($departamento_gerido != null) {
            var.update $departamento_gerido_id {
              value = $departamento_gerido.id
            }
          }
        }
      }
    }

    db.query colaborador {
      where = $db.colaborador.anonimizado_em == null
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "departamento_id", "cargo_id", "status", "superior_colaborador_id", "data_admissao", "user_id"]
    } as $todos_colaboradores

    var $visiveis {
      value = []
    }

    var $ids_visiveis {
      value = []
    }

    foreach ($todos_colaboradores) {
      each as $c {
        var $e_eu {
          value = ($colaborador_autenticado != null && $c.id == $colaborador_autenticado.id)
        }

        var $posso_ver {
          value = ($ve_todos || $e_eu || ($colaborador_autenticado != null && ($c.superior_colaborador_id == $colaborador_autenticado.id || ($c.superior_colaborador_id == null && $departamento_gerido_id != null && $c.departamento_id == $departamento_gerido_id))))
        }

        conditional {
          if ($posso_ver) {
            var.update $visiveis {
              value = $visiveis|push:$c
            }

            var.update $ids_visiveis {
              value = $ids_visiveis|push:$c.id
            }
          }
        }
      }
    }

    precondition ($colaborador_autenticado == null || $input.colaborador_id != $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao pode ajustar o proprio ponto: peca a correcao, que vai para o seu superior."
    }

    precondition ($ids_visiveis|contains:$input.colaborador_id) {
      error_type = "accessdenied"
      error = "Voce nao pode ajustar o ponto desta pessoa."
    }

    precondition ($input.campo == "hora_entrada" || $input.campo == "inicio_intervalo" || $input.campo == "fim_intervalo" || $input.campo == "hora_saida") {
      error_type = "inputerror"
      error = "Campo invalido. Use hora_entrada, inicio_intervalo, fim_intervalo ou hora_saida."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    var $hoje_brasilia {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition ($input.data <= $hoje_brasilia) {
      error_type = "inputerror"
      error = "Nao e possivel ajustar um dia futuro."
    }

    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $input.colaborador_id && $db.registro_ponto.data == $input.data
      return = {type: "single"}
    } as $registro_existente

    conditional {
      if ($registro_existente == null) {
        db.add registro_ponto {
          data = {
            colaborador_id: $input.colaborador_id
            data          : $input.data
            status        : "Incompleto"
            observacao    : "Criado por ajuste do gestor ou do RH."
            updated_at    : "now"
          }
        } as $registro_criado
      }
    }

    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $input.colaborador_id && $db.registro_ponto.data == $input.data
      return = {type: "single"}
    } as $registro_alvo

    db.query correcao_ponto {
      where = $db.correcao_ponto.registro_ponto_id == $registro_alvo.id && $db.correcao_ponto.campo == $input.campo && $db.correcao_ponto.status == "pendente"
      return = {type: "single"}
    } as $pedido_pendente

    precondition ($pedido_pendente == null) {
      error_type = "inputerror"
      error = "Ha um pedido de correcao pendente para esta marcacao: aprove ou recuse o pedido."
    }
    // Horario pedido: dentro da janela do dia e nunca no futuro. A janela vai da meia-noite
    // UTC do dia ate as 06:00 (Brasilia) do dia seguinte, para cobrir a virada de data
    // em UTC do registro (tarefa 73) e jornadas que passam da meia-noite.
    var $inicio_janela {
      value = ($input.data|to_timestamp)
    }

    var $fim_janela {
      value = $inicio_janela + 86400000 + 32400000
    }

    precondition ($input.valor_solicitado >= $inicio_janela && $input.valor_solicitado <= $fim_janela) {
      error_type = "inputerror"
      error = "O horario pedido precisa ser do mesmo dia do registro."
    }

    precondition ($input.valor_solicitado <= now) {
      error_type = "inputerror"
      error = "O horario pedido nao pode ser no futuro."
    }

    // Ordem das marcacoes: entrada < saida para o almoco < volta < saida. O horario pedido
    // precisa ficar depois da marcacao anterior e antes da seguinte que ja existem.
    var $limite_inferior {
      value = null
    }

    var $limite_superior {
      value = null
    }

    conditional {
      if ($input.campo == "hora_entrada") {
        var.update $limite_superior {
          value = ($registro_alvo.inicio_intervalo != null ? $registro_alvo.inicio_intervalo : ($registro_alvo.fim_intervalo != null ? $registro_alvo.fim_intervalo : $registro_alvo.hora_saida))
        }
      }
    }

    conditional {
      if ($input.campo == "inicio_intervalo") {
        var.update $limite_inferior {
          value = $registro_alvo.hora_entrada
        }

        var.update $limite_superior {
          value = ($registro_alvo.fim_intervalo != null ? $registro_alvo.fim_intervalo : $registro_alvo.hora_saida)
        }
      }
    }

    conditional {
      if ($input.campo == "fim_intervalo") {
        var.update $limite_inferior {
          value = ($registro_alvo.inicio_intervalo != null ? $registro_alvo.inicio_intervalo : $registro_alvo.hora_entrada)
        }

        var.update $limite_superior {
          value = $registro_alvo.hora_saida
        }
      }
    }

    conditional {
      if ($input.campo == "hora_saida") {
        var.update $limite_inferior {
          value = ($registro_alvo.fim_intervalo != null ? $registro_alvo.fim_intervalo : ($registro_alvo.inicio_intervalo != null ? $registro_alvo.inicio_intervalo : $registro_alvo.hora_entrada))
        }
      }
    }

    precondition ($limite_inferior == null || $input.valor_solicitado > $limite_inferior) {
      error_type = "inputerror"
      error = "O horario pedido precisa ser depois da marcacao anterior do dia."
    }

    precondition ($limite_superior == null || $input.valor_solicitado < $limite_superior) {
      error_type = "inputerror"
      error = "O horario pedido precisa ser antes da marcacao seguinte do dia."
    }


    var $valor_original_atual {
      value = ($input.campo == "hora_entrada" ? $registro_alvo.hora_entrada : ($input.campo == "inicio_intervalo" ? $registro_alvo.inicio_intervalo : ($input.campo == "fim_intervalo" ? $registro_alvo.fim_intervalo : $registro_alvo.hora_saida)))
    }

    db.transaction {
      stack {
        conditional {
          if ($input.campo == "hora_entrada") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {hora_entrada: $input.valor_solicitado, updated_at: "now"}
            } as $editado_1
          }
        }

        conditional {
          if ($input.campo == "inicio_intervalo") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {inicio_intervalo: $input.valor_solicitado, updated_at: "now"}
            } as $editado_2
          }
        }

        conditional {
          if ($input.campo == "fim_intervalo") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {fim_intervalo: $input.valor_solicitado, updated_at: "now"}
            } as $editado_3
          }
        }

        conditional {
          if ($input.campo == "hora_saida") {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_alvo.id
              data = {hora_saida: $input.valor_solicitado, updated_at: "now"}
            } as $editado_4
          }
        }

        db.get registro_ponto {
          field_name = "id"
          field_value = $registro_alvo.id
        } as $registro_depois

        var $todos_presentes {
          value = ($registro_depois.hora_entrada != null && $registro_depois.inicio_intervalo != null && $registro_depois.fim_intervalo != null && $registro_depois.hora_saida != null)
        }

        conditional {
          if ($todos_presentes) {
            var $horas_recalculadas {
              value = (($registro_depois.hora_saida - $registro_depois.hora_entrada) - ($registro_depois.fim_intervalo - $registro_depois.inicio_intervalo)) / 3600000
            }

            db.query regra_contrato {
              where = $db.regra_contrato.tipo_contrato == $colaborador_alvo.tipo_contrato && $db.regra_contrato.ativo == true
              return = {type: "single"}
            } as $regra_ajuste

            var $extras_recalculadas {
              value = 0
            }

            conditional {
              if ($regra_ajuste != null && $regra_ajuste.permite_hora_extra == true && $regra_ajuste.horas_diarias != null && $horas_recalculadas > $regra_ajuste.horas_diarias) {
                var.update $extras_recalculadas {
                  value = $horas_recalculadas - $regra_ajuste.horas_diarias
                }
              }
            }

            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_depois.id
              data = {horas_trabalhadas: $horas_recalculadas, horas_extras: $extras_recalculadas, status: "Ajustado", updated_at: "now"}
            } as $final_completo
          }
        }

        conditional {
          if ($todos_presentes == false) {
            db.edit registro_ponto {
              field_name = "id"
              field_value = $registro_depois.id
              data = {status: "Ajustado", updated_at: "now"}
            } as $final_incompleto
          }
        }

        // Historico: o ajuste fica como correcao ja aprovada, com quem fez e o motivo.
        db.add correcao_ponto {
          data = {
            registro_ponto_id   : $registro_alvo.id
            colaborador_id       : $input.colaborador_id
            campo                 : $input.campo
            valor_original         : $valor_original_atual
            valor_solicitado        : $input.valor_solicitado
            justificativa            : "Ajuste direto: " ~ $input.motivo
            status                    : "aprovada"
            decidido_por_user_id       : $usuario_autenticado.id
            data_decisao                : "now"
            motivo_decisao               : $input.motivo
            updated_at                    : "now"
          }
        } as $ajuste_registrado

        db.add auditoria {
          data = {
            user_id       : $usuario_autenticado.id
            acao          : "ajustar_ponto"
            recurso       : "registro_ponto"
            registro_id   : $registro_alvo.id
            justificativa : $input.motivo
            valor_anterior: ($valor_original_atual|to_text)
            valor_novo    : ($input.valor_solicitado|to_text)
            resultado     : "sucesso"
          }
        } as $evento_auditoria
      }
    }

    // Avisa a pessoa (quando ela tem conta).
    conditional {
      if ($colaborador_alvo.user_id != null) {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $colaborador_alvo.user_id
            tipo                : "ponto_ajustado"
            titulo              : "Seu ponto foi ajustado"
            mensagem            : "Uma marcacao do dia " ~ $input.data ~ " foi ajustada. Motivo: " ~ $input.motivo
            recurso             : "registro_ponto"
            registro_id         : $registro_alvo.id
          }
        } as $aviso_ajuste
      }
    }
  }

  response = {
    sucesso    : true
    mensagem   : "Ajuste aplicado. A pessoa foi avisada."
    registro_id: $registro_alvo.id
  }

  guid = "conectahr-folha-ponto-ajustar-post-0001"
}
