// Conclui uma meta com resultado final. RH/ADMIN ou o Gestor do
// departamento do colaborador podem concluir.
query "metas/{id}/concluir" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    decimal resultado_final filters=max:100
    text? comentario_final? filters=trim|max:2000
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
      error = "Esta meta ja esta concluida ou cancelada."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $meta_atual.colaborador_id
    } as $colaborador_da_meta

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $e_gestor_da_equipe {
      value = false
    }

    conditional {
      if ($perfil_autenticado == "GESTOR" && $colaborador_autenticado != null && $colaborador_da_meta != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerenciado

        conditional {
          if ($departamento_gerenciado != null && $colaborador_da_meta.departamento_id == $departamento_gerenciado.id) {
            var.update $e_gestor_da_equipe {
              value = true
            }
          }
        }
      }
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_gestor_da_equipe) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para concluir esta meta."
    }

    db.edit meta_avaliacao {
      field_name = "id"
      field_value = $meta_atual.id
      data = {
        resultado_final : $input.resultado_final
        comentario_final: $input.comentario_final
        status          : "concluida"
        updated_at      : "now"
      }
    } as $meta_concluida
  }

  response = {
    sucesso : true
    mensagem: "Meta concluida com sucesso."
    meta    : $meta_concluida
  }

  guid = "conectahr-metas-concluir-post-0001"
}
