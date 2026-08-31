// Consulta o saldo de banco de horas de um colaborador (soma de
// creditos menos debitos) e o extrato de lancamentos. O saldo continua
// consultavel apos o desligamento do colaborador (nenhum lancamento e
// apagado), cobrindo a consulta de saldo na rescisao. Acesso: RH/ADMIN
// (qualquer colaborador), o proprio colaborador, ou o Gestor da equipe.
query "colaboradores/{id}/banco_horas" verb=GET {
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
      error = "Voce nao tem permissao para consultar este banco de horas."
    }

    db.query banco_horas_lancamento {
      where = $db.banco_horas_lancamento.colaborador_id == $colaborador_alvo.id
      sort = {banco_horas_lancamento.data_lancamento: "desc"}
      return = {type: "list"}
    } as $lancamentos

    var $saldo {
      value = 0
    }

    foreach ($lancamentos) {
      each as $lancamento_item {
        conditional {
          if ($lancamento_item.tipo == "credito") {
            var.update $saldo {
              value = $saldo + $lancamento_item.horas
            }
          }
        }

        conditional {
          if ($lancamento_item.tipo == "debito") {
            var.update $saldo {
              value = $saldo - $lancamento_item.horas
            }
          }
        }
      }
    }
  }

  response = {
    sucesso     : true
    saldo_horas : $saldo
    lancamentos : $lancamentos
  }

  guid = "conectahr-colaboradores-banco-horas-get-0001"
}
