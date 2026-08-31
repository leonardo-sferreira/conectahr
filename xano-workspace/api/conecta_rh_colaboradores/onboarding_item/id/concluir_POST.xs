// Conclui uma etapa do onboarding. So o responsavel definido para a
// etapa pode concluir (rh, o proprio colaborador, ou o gestor do seu
// departamento) - impede conclusao indevida fora do fluxo (Requirement
// "Onboarding de colaborador", cenario "Item de onboarding concluido").
query "onboarding_item/{id}/concluir" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text? evidencia? filters=trim|max:500
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

    // Notfound de item/onboarding e o estado "ja concluido" ficam
    // deferidos para depois da checagem de autorizacao abaixo, para nao
    // vazar existencia/estado de um item a quem nao e o responsavel por ele.
    db.get onboarding_item {
      field_name = "id"
      field_value = $input.id
    } as $item_atual

    db.get onboarding {
      field_name = "id"
      field_value = $item_atual.onboarding_id
    } as $onboarding_do_item

    db.get colaborador {
      field_name = "id"
      field_value = $onboarding_do_item.colaborador_id
    } as $colaborador_do_onboarding

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    // Verifica se o usuario autenticado e o responsavel autorizado por este item.
    var $autorizado {
      value = false
    }

    conditional {
      if ($item_atual != null && $item_atual.responsavel == "rh" && ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")) {
        var.update $autorizado {
          value = true
        }
      }
    }

    conditional {
      if ($item_atual != null && $item_atual.responsavel == "colaborador" && $colaborador_do_onboarding != null && $colaborador_do_onboarding.user_id == $usuario_autenticado.id) {
        var.update $autorizado {
          value = true
        }
      }
    }

    conditional {
      if ($item_atual != null && $item_atual.responsavel == "gestor" && $perfil_autenticado == "GESTOR" && $colaborador_do_onboarding != null) {
        db.get colaborador {
          field_name = "user_id"
          field_value = $usuario_autenticado.id
        } as $colaborador_gestor

        conditional {
          if ($colaborador_gestor != null) {
            db.query departamento {
              where = $db.departamento.gestor_colaborador_id == $colaborador_gestor.id
              return = {type: "single"}
            } as $departamento_gerenciado

            conditional {
              if ($departamento_gerenciado != null && $colaborador_do_onboarding.departamento_id == $departamento_gerenciado.id) {
                var.update $autorizado {
                  value = true
                }
              }
            }
          }
        }
      }
    }

    // RH e ADMIN sempre podem concluir em nome de qualquer responsavel (supervisao).
    conditional {
      if ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
        var.update $autorizado {
          value = true
        }
      }
    }

    precondition ($autorizado) {
      error_type = "accessdenied"
      error = "Voce nao e o responsavel por este item de onboarding."
    }

    // So chega aqui autorizado — agora sim e seguro confirmar existencia e estado.
    precondition ($item_atual != null) {
      error_type = "notfound"
      error = "Item de onboarding nao encontrado."
    }

    precondition ($onboarding_do_item != null) {
      error_type = "notfound"
      error = "Onboarding relacionado nao encontrado."
    }

    precondition ($item_atual.concluido == false) {
      error_type = "inputerror"
      error = "Este item ja esta concluido."
    }

    db.edit onboarding_item {
      field_name = "id"
      field_value = $item_atual.id
      data = {
        concluido           : true
        concluido_por_user_id : $usuario_autenticado.id
        concluido_em           : "now"
        evidencia               : $input.evidencia
        updated_at               : "now"
      }
    } as $item_concluido

    // Auditoria: conclusao de item de onboarding.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "concluir_item_onboarding"
        recurso    : "onboarding_item"
        registro_id: $item_atual.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Item de onboarding concluido com sucesso."
    item    : $item_concluido
  }

  guid = "conectahr-onboarding-item-concluir-post-0001"
}
