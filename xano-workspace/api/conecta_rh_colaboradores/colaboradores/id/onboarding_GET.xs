// Consulta o onboarding de um colaborador com o checklist e o
// progresso calculado. Acesso: RH/ADMIN (qualquer colaborador), o
// proprio colaborador, ou o Gestor do departamento do colaborador.
query "colaboradores/{id}/onboarding" verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    // Nao ha precondition de notfound aqui de proposito: para um chamador
    // sem RH/ADMIN/vinculo, "colaborador nao existe" e "colaborador existe
    // mas voce nao tem acesso" devem responder igual (accessdenied),
    // senao a existencia de um colaborador especifico (inclusive
    // Desligado, que buscar_GET.xs esconde de quem nao e RH/ADMIN) vaza
    // para qualquer usuario autenticado antes da checagem de autorizacao.
    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo != null && $colaborador_alvo.user_id == $usuario_autenticado.id)
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
          if ($departamento_gerenciado != null && $colaborador_alvo != null && $colaborador_alvo.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_da_equipe {
              value = true
            }
          }
        }
      }
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio || $e_gestor_da_equipe) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar este onboarding."
    }

    // So chega aqui autorizado (RH/ADMIN, dono, ou gestor da equipe) —
    // agora sim e seguro confirmar se o colaborador existe.
    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    db.query onboarding {
      where = $db.onboarding.colaborador_id == $colaborador_alvo.id
      return = {type: "single"}
    } as $onboarding_encontrado

    precondition ($onboarding_encontrado != null) {
      error_type = "notfound"
      error = "Este colaborador ainda nao tem onboarding iniciado."
    }

    db.query onboarding_item {
      where = $db.onboarding_item.onboarding_id == $onboarding_encontrado.id
      sort = {onboarding_item.id: "asc"}
      return = {type: "list"}
    } as $itens

    var $total_itens {
      value = ($itens|count)
    }

    var $itens_concluidos {
      value = 0
    }

    foreach ($itens) {
      each as $item {
        conditional {
          if ($item.concluido) {
            var.update $itens_concluidos {
              value = $itens_concluidos + 1
            }
          }
        }
      }
    }

    var $percentual_concluido {
      value = ((($itens_concluidos * 100) / $total_itens)|to_int)
    }
  }

  response = {
    sucesso              : true
    onboarding             : $onboarding_encontrado
    itens                   : $itens
    total_itens              : $total_itens
    itens_concluidos          : $itens_concluidos
    percentual_concluido       : $percentual_concluido
  }

  guid = "conectahr-colaboradores-onboarding-get-0001"
}
