// Calendario organizacional: feriados (sempre visiveis a todos),
// ferias aprovadas e ausencias aprovadas do departamento do usuario
// (RH/ADMIN veem de todos os departamentos).
query calendario verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    db.query feriado {
      where = $db.feriado.ativo == true
      sort = {feriado.data: "asc"}
      return = {type: "list"}
    } as $feriados

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $departamento_escopo_id {
      value = null
    }

    conditional {
      if (($perfil_autenticado == "GESTOR" || $perfil_autenticado == "COLABORADOR") && $colaborador_autenticado != null) {
        var.update $departamento_escopo_id {
          value = $colaborador_autenticado.departamento_id
        }
      }
    }

    db.query ferias {
      where = $db.ferias.status == "Aprovada"
      return = {type: "list"}
    } as $ferias_aprovadas_todas

    db.query ausencia {
      where = $db.ausencia.status == "Aprovada"
      return = {type: "list"}
    } as $ausencias_aprovadas_todas

    var $ferias_no_escopo {
      value = []
    }

    var $ausencias_no_escopo {
      value = []
    }

    conditional {
      if ($departamento_escopo_id == null) {
        var.update $ferias_no_escopo {
          value = $ferias_aprovadas_todas
        }

        var.update $ausencias_no_escopo {
          value = $ausencias_aprovadas_todas
        }
      }
    }

    conditional {
      if ($departamento_escopo_id != null) {
        foreach ($ferias_aprovadas_todas) {
          each as $ferias_item {
            db.get colaborador {
              field_name = "id"
              field_value = $ferias_item.colaborador_id
            } as $colaborador_da_ferias

            conditional {
              if ($colaborador_da_ferias != null && $colaborador_da_ferias.departamento_id == $departamento_escopo_id) {
                var.update $ferias_no_escopo {
                  value = $ferias_no_escopo|push:$ferias_item
                }
              }
            }
          }
        }

        foreach ($ausencias_aprovadas_todas) {
          each as $ausencia_item {
            db.get colaborador {
              field_name = "id"
              field_value = $ausencia_item.colaborador_id
            } as $colaborador_da_ausencia

            conditional {
              if ($colaborador_da_ausencia != null && $colaborador_da_ausencia.departamento_id == $departamento_escopo_id) {
                var.update $ausencias_no_escopo {
                  value = $ausencias_no_escopo|push:$ausencia_item
                }
              }
            }
          }
        }
      }
    }

    // Ausencias na resposta: SO tipo, periodo e status (LGPD). Motivo, observacao e
    // comprovante sao dado de saude e nunca saem por aqui, nem para o Gestor.
    var $ausencias_resposta {
      value = []
    }

    foreach ($ausencias_no_escopo) {
      each as $ausencia_visivel {
        var.update $ausencias_resposta {
          value = $ausencias_resposta|push:{id: $ausencia_visivel.id, colaborador_id: $ausencia_visivel.colaborador_id, tipo: $ausencia_visivel.tipo, data_inicio: $ausencia_visivel.data_inicio, data_fim: $ausencia_visivel.data_fim, status: $ausencia_visivel.status}
        }
      }
    }
  }

  response = {
    sucesso   : true
    feriados  : $feriados
    ferias    : $ferias_no_escopo
    ausencias : $ausencias_resposta
  }

  guid = "conectahr-calendario-get-0001"
}
