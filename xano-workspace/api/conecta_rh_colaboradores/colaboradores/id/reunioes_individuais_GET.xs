// Consulta o historico de reunioes individuais de um colaborador.
// O colaborador ve as proprias (participante); o Gestor autor ve as
// que registrou; RH/ADMIN veem somente as marcadas `compartilhado_rh`
// (as `privado` ficam so entre gestor e colaborador).
query "colaboradores/{id}/reunioes_individuais" verb=GET {
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

    precondition ($e_o_proprio || $perfil_autenticado == "GESTOR" || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar estas reunioes."
    }

    db.query reuniao_individual {
      where = $db.reuniao_individual.colaborador_id == $colaborador_alvo.id
      sort = {reuniao_individual.data_reuniao: "desc"}
      return = {type: "list"}
    } as $reunioes_todas

    var $reunioes_visiveis {
      value = []
    }

    foreach ($reunioes_todas) {
      each as $reuniao_item {
        var $visivel {
          value = ($e_o_proprio) || ($reuniao_item.gestor_user_id == $usuario_autenticado.id) || (($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") && $reuniao_item.visibilidade == "compartilhado_rh")
        }

        conditional {
          if ($visivel) {
            var.update $reunioes_visiveis {
              value = $reunioes_visiveis|push:$reuniao_item
            }
          }
        }
      }
    }
  }

  response = {
    sucesso  : true
    reunioes : $reunioes_visiveis
  }

  guid = "conectahr-colaboradores-reunioes-individuais-get-0001"
}
