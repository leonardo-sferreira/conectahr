// Registra o proximo marcador de ponto do dia para o colaborador autenticado.
// Ordem: entrada -> inicio do intervalo -> fim do intervalo -> saida.
// Cria o registro do dia na primeira marcacao (entrada) e calcula as
// horas trabalhadas quando a saida e registrada.
query "ponto/marcar" verb=POST {
  api_group = "ConectaRH - Ponto"
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

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Localiza o colaborador vinculado a conta autenticada.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }

    // Somente colaborador profissionalmente ativo pode registrar ponto.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }

    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem registrar ponto."
    }

    // Bloqueia inicio operacional de admissao CLT sem eSocial/CTPS
    // confirmados (item 3.5). So se aplica quando ha um registro de
    // admissao CLT rastreado; nao bloqueia colaboradores anteriores a
    // esse rastreio (esocial_status/ctps_status nulos).
    conditional {
      if ($colaborador_autenticado.tipo_contrato == "CLT") {
        db.query historico_profissional {
          where = $db.historico_profissional.colaborador_id == $colaborador_autenticado.id && $db.historico_profissional.tipo_alteracao == "admissao"
          return = {type: "single"}
        } as $admissao_clt

        var $esocial_pendente {
          value = ($admissao_clt != null && $admissao_clt.esocial_status != null && $admissao_clt.esocial_status != "confirmado")
        }

        var $ctps_pendente {
          value = ($admissao_clt != null && $admissao_clt.ctps_status != null && $admissao_clt.ctps_status != "confirmado")
        }

        precondition ($esocial_pendente == false && $ctps_pendente == false) {
          error_type = "accessdenied"
          error = "Registro eSocial ou anotacao na CTPS Digital da admissao ainda nao confirmados. Contate o RH."
        }
      }
    }

    // Data de hoje, usada para localizar ou criar o registro do dia.
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    // Localiza o registro de ponto do dia, se existir.
    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colaborador_autenticado.id && $db.registro_ponto.data == $hoje
      return = {type: "single"}
    } as $registro_hoje

    // Guarda o id do registro final, definido em um dos ramos abaixo.
    var $registro_ponto_id {
      value = 0
    }

    // Ramo 1: primeira marcacao do dia, registra a entrada.
    conditional {
      if ($registro_hoje == null) {
        db.add registro_ponto {
          data = {
            colaborador_id: $colaborador_autenticado.id
            data          : $hoje
            hora_entrada  : now
            status        : "Aberto"
            updated_at    : "now"
          }
        } as $registro_criado

        var.update $registro_ponto_id {
          value = $registro_criado.id
        }
      }
    }

    // Ramo 2: segunda marcacao, inicio do intervalo.
    conditional {
      if ($registro_hoje != null && $registro_hoje.inicio_intervalo == null) {
        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_hoje.id
          data = {inicio_intervalo: now, updated_at: "now"}
        } as $registro_intervalo_iniciado

        var.update $registro_ponto_id {
          value = $registro_intervalo_iniciado.id
        }
      }
    }

    // Ramo 3: terceira marcacao, fim do intervalo.
    conditional {
      if ($registro_hoje != null && $registro_hoje.inicio_intervalo != null && $registro_hoje.fim_intervalo == null) {
        // Intervalo minimo da matriz (item 4.13) — bloqueia fechar o
        // intervalo antes do minimo, sem override aprovado.
        db.query regra_contrato {
          where = $db.regra_contrato.tipo_contrato == $colaborador_autenticado.tipo_contrato && $db.regra_contrato.ativo == true
          return = {type: "single"}
        } as $regra_intervalo

        var $inicio_intervalo_extraido {
          value = $registro_hoje.inicio_intervalo
        }

        var $agora_intervalo {
          value = now
        }

        var $duracao_intervalo_atual_min {
          value = (($agora_intervalo - $inicio_intervalo_extraido) / 60000)
        }

        conditional {
          if ($regra_intervalo != null && $regra_intervalo.intervalo_minutos != null && $duracao_intervalo_atual_min < $regra_intervalo.intervalo_minutos) {
            function.run "ConectaHR/resolver_regra" {
              input = {colaborador_id: $colaborador_autenticado.id, parametro: "intervalo_minutos"}
            } as $resolucao_intervalo

            precondition ($resolucao_intervalo.override_aplicado != null) {
              error_type = "accessdenied"
              error = "O intervalo minimo da matriz ainda nao foi cumprido e nao ha override aprovado para este colaborador."
            }
          }
        }

        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_hoje.id
          data = {fim_intervalo: now, updated_at: "now"}
        } as $registro_intervalo_finalizado

        var.update $registro_ponto_id {
          value = $registro_intervalo_finalizado.id
        }
      }
    }

    // Ramo 4: quarta marcacao, saida. Calcula as horas trabalhadas.
    conditional {
      if ($registro_hoje != null && $registro_hoje.fim_intervalo != null && $registro_hoje.hora_saida == null) {
        var $hora_entrada_extraida {
          value = $registro_hoje.hora_entrada
        }

        var $agora_saida {
          value = now
        }

        var $duracao_bruta_ms {
          value = ($agora_saida - $hora_entrada_extraida)
        }

        var $duracao_intervalo_ms {
          value = $registro_hoje.fim_intervalo - $registro_hoje.inicio_intervalo
        }

        var $duracao_trabalhada_ms {
          value = $duracao_bruta_ms - $duracao_intervalo_ms
        }

        var $horas_trabalhadas_calculadas {
          value = $duracao_trabalhada_ms / 3600000
        }

        // Horas extras parametrizadas pela matriz regra_contrato (item
        // 4.1) — so calcula, nao bloqueia (bloqueio de excesso sobre o
        // limite fica para o motor de regras da tarefa 4.13).
        db.query regra_contrato {
          where = $db.regra_contrato.tipo_contrato == $colaborador_autenticado.tipo_contrato && $db.regra_contrato.ativo == true
          return = {type: "single"}
        } as $regra_ponto_saida

        var $horas_extras_calculadas {
          value = 0
        }

        conditional {
          if ($regra_ponto_saida != null && $regra_ponto_saida.permite_hora_extra == true && $regra_ponto_saida.horas_diarias != null && $horas_trabalhadas_calculadas > $regra_ponto_saida.horas_diarias) {
            var.update $horas_extras_calculadas {
              value = $horas_trabalhadas_calculadas - $regra_ponto_saida.horas_diarias
            }
          }
        }

        // Bloqueia horas extras acima do limite da matriz sem override
        // aprovado (item 4.13) — a presenca de uma regra_override
        // vigente para limite_hora_extra_diaria aplicavel a este
        // colaborador e a autorizacao (o valor exato ja foi decidido no
        // fluxo de aprovacao do override; aqui so se verifica que existe).
        conditional {
          if ($regra_ponto_saida != null && $regra_ponto_saida.limite_hora_extra_diaria != null && $horas_extras_calculadas > $regra_ponto_saida.limite_hora_extra_diaria) {
            function.run "ConectaHR/resolver_regra" {
              input = {colaborador_id: $colaborador_autenticado.id, parametro: "limite_hora_extra_diaria"}
            } as $resolucao_limite_extra

            precondition ($resolucao_limite_extra.override_aplicado != null) {
              error_type = "accessdenied"
              error = "Horas extras excedem o limite diario da matriz e nao ha override aprovado para este colaborador. Registre a saida com o RH."
            }
          }
        }

        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_hoje.id
          data = {
            hora_saida       : now
            horas_trabalhadas: $horas_trabalhadas_calculadas
            horas_extras     : $horas_extras_calculadas
            status           : "Completo"
            updated_at       : "now"
          }
        } as $registro_finalizado

        var.update $registro_ponto_id {
          value = $registro_finalizado.id
        }
      }
    }

    // Ramo 5: todos os quatro marcadores do dia ja foram registrados.
    conditional {
      if ($registro_hoje != null && $registro_hoje.hora_saida != null) {
        precondition (false) {
          error_type = "inputerror"
          error = "Todos os marcadores de ponto de hoje ja foram registrados."
        }
      }
    }

    // Recarrega o registro final para a resposta.
    db.get registro_ponto {
      field_name = "id"
      field_value = $registro_ponto_id
    } as $registro_atualizado
  }

  response = {
    sucesso : true
    mensagem: "Marcacao de ponto registrada com sucesso."
    registro: $registro_atualizado
  }

  guid = "conectahr-ponto-marcar-0001"
}
