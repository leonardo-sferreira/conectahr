// Registra um check-in de progresso na meta: percentual, comentario,
// dificuldades, evidencia e alteracao de prazo. Cada chamada cria um
// evento na trilha `meta_checkin` (historico completo, nunca sobrescrito)
// e atualiza o "ultimo check-in" em `meta_avaliacao` para consulta
// rapida. O proprio colaborador (dono da meta) ou RH/ADMIN podem
// registrar.
query "metas/{id}/checkin" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    decimal progresso_percentual filters=min:0|max:100
    text? comentario_checkin? filters=trim|max:2000
    text? dificuldades? filters=trim|max:2000
    text? evidencia? filters=trim|max:1000
    date? novo_prazo?
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get meta_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $meta_atual

    precondition ($meta_atual != null) {
      error_type = "notfound"
      error = "Meta nao encontrada."
    }

    precondition ($meta_atual.status != "concluida" && $meta_atual.status != "cancelada") {
      error_type = "inputerror"
      error = "Nao e possivel registrar check-in em meta concluida ou cancelada."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $meta_atual.colaborador_id
    } as $colaborador_da_meta

    var $e_o_proprio {
      value = ($colaborador_da_meta != null && $colaborador_da_meta.user_id == $usuario_autenticado.id)
    }

    precondition ($e_o_proprio || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para registrar check-in nesta meta."
    }

    // Se um novo prazo foi informado, usa-o; senao preserva o atual.
    var $prazo_final {
      value = $meta_atual.data_prazo
    }

    conditional {
      if ($input.novo_prazo != null) {
        var.update $prazo_final {
          value = $input.novo_prazo
        }
      }
    }

    db.transaction {
      stack {
        db.edit meta_avaliacao {
          field_name = "id"
          field_value = $meta_atual.id
          data = {
            progresso_percentual   : $input.progresso_percentual
            comentario_checkin       : $input.comentario_checkin
            data_checkin_realizado      : "now"
            data_prazo                     : $prazo_final
            status                            : "em_andamento"
            updated_at                           : "now"
          }
        } as $meta_atualizada

        db.add meta_checkin {
          data = {
            meta_avaliacao_id     : $meta_atual.id
            registrado_por_user_id  : $usuario_autenticado.id
            progresso_percentual      : $input.progresso_percentual
            comentario                   : $input.comentario_checkin
            dificuldades                    : $input.dificuldades
            evidencia                          : $input.evidencia
            novo_prazo                            : $input.novo_prazo
          }
        } as $checkin_criado
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Check-in registrado com sucesso."
    meta    : $meta_atualizada
  }

  guid = "conectahr-metas-checkin-post-0001"
}
