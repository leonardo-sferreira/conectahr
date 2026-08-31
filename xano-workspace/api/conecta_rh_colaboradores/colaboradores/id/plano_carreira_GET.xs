// Consulta o plano de carreira do colaborador: nivel atual, proximo
// nivel, competencias esperadas para o proximo nivel (lacunas a
// desenvolver), metas ativas, PDI ativo e historico de evolucao
// (admissao/promocoes/alteracoes de cargo). Nunca promove automaticamente
// - so exibe informacao. Acesso: o proprio colaborador, RH/ADMIN, ou o
// Gestor da equipe.
query "colaboradores/{id}/plano_carreira" verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo.user_id == $usuario_autenticado.id)
    }

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
          if ($departamento_gerenciado != null && $colaborador_alvo.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_da_equipe {
              value = true
            }
          }
        }
      }
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio || $e_gestor_da_equipe) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar este plano de carreira."
    }

    // Determina o proximo nivel (nunca promove - so informa qual seria).
    var $proximo_nivel {
      value = null
    }

    conditional {
      if ($colaborador_alvo.nivel == "l1") {
        var.update $proximo_nivel {
          value = "l2"
        }
      }
    }

    conditional {
      if ($colaborador_alvo.nivel == "l2") {
        var.update $proximo_nivel {
          value = "l3"
        }
      }
    }

    conditional {
      if ($colaborador_alvo.nivel == "l3") {
        var.update $proximo_nivel {
          value = "l4"
        }
      }
    }

    conditional {
      if ($colaborador_alvo.nivel == "l4") {
        var.update $proximo_nivel {
          value = "l5"
        }
      }
    }

    var $competencias_proximo_nivel {
      value = []
    }

    conditional {
      if ($proximo_nivel != null) {
        db.query competencia_avaliacao {
          where = $db.competencia_avaliacao.nivel == $proximo_nivel && $db.competencia_avaliacao.ativo == true
          return = {type: "list"}
        } as $competencias_encontradas

        var.update $competencias_proximo_nivel {
          value = $competencias_encontradas
        }
      }
    }

    db.query meta_avaliacao {
      where = $db.meta_avaliacao.colaborador_id == $colaborador_alvo.id && $db.meta_avaliacao.status != "concluida" && $db.meta_avaliacao.status != "cancelada"
      return = {type: "list"}
    } as $metas_ativas

    db.query pdi {
      where = $db.pdi.colaborador_id == $colaborador_alvo.id && $db.pdi.status != "concluido" && $db.pdi.status != "cancelado"
      return = {type: "list"}
    } as $pdi_ativo

    db.query historico_profissional {
      where = $db.historico_profissional.colaborador_id == $colaborador_alvo.id
      sort = {historico_profissional.data_inicio: "asc"}
      return = {type: "list"}
    } as $historico_evolucao
  }

  response = {
    sucesso                    : true
    nivel_atual                 : $colaborador_alvo.nivel
    proximo_nivel                 : $proximo_nivel
    competencias_proximo_nivel     : $competencias_proximo_nivel
    metas_ativas                     : $metas_ativas
    pdi_ativo                          : $pdi_ativo
    historico_evolucao                   : $historico_evolucao
  }

  guid = "conectahr-colaboradores-plano-carreira-get-0001"
}
