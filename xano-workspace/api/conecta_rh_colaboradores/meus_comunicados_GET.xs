// Lista os comunicados vigentes visiveis para o usuario autenticado:
// publico_alvo "todos", ou "departamento" (do proprio colaborador), ou
// "perfil" (do proprio perfil).
query "meus_comunicados" verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    // Comunicados ativos e dentro da vigencia.
    db.query comunicado {
      where = $db.comunicado.ativo == true && $db.comunicado.data_inicio <= $hoje && ($db.comunicado.data_fim == null || $db.comunicado.data_fim >= $hoje)
      sort = {comunicado.created_at: "desc"}
      return = {type: "list"}
    } as $comunicados_vigentes

    var $meus_comunicados {
      value = []
    }

    foreach ($comunicados_vigentes) {
      each as $comunicado_item {
        var $visivel {
          value = ($comunicado_item.publico_alvo == "todos") || ($comunicado_item.publico_alvo == "perfil" && ($comunicado_item.perfil_alvo|trim|to_upper) == $perfil_autenticado) || ($comunicado_item.publico_alvo == "departamento" && $colaborador_autenticado != null && $comunicado_item.departamento_id == $colaborador_autenticado.departamento_id)
        }

        conditional {
          if ($visivel) {
            var.update $meus_comunicados {
              value = $meus_comunicados|push:$comunicado_item
            }
          }
        }
      }
    }
  }

  response = {
    sucesso    : true
    comunicados: $meus_comunicados
  }

  guid = "conectahr-meus-comunicados-get-0001"
}
