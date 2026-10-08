// Consulta a trilha completa de check-ins de uma meta. Acesso: dono da
// meta, RH/ADMIN, ou o Gestor do departamento do colaborador.
query "metas/{id}/checkins" verb=GET {
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

    db.get meta_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $meta_atual

    precondition ($meta_atual != null) {
      error_type = "notfound"
      error = "Meta nao encontrada."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get colaborador {
      field_name = "id"
      field_value = $meta_atual.colaborador_id
    } as $colaborador_da_meta

    var $e_o_proprio {
      value = ($colaborador_da_meta != null && $colaborador_da_meta.user_id == $usuario_autenticado.id)
    }

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

    precondition ($e_o_proprio || $e_gestor_da_equipe || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar este historico."
    }

    db.query meta_checkin {
      where = $db.meta_checkin.meta_avaliacao_id == $meta_atual.id
      sort = {meta_checkin.created_at: "asc"}
      return = {type: "list"}
    } as $checkins
  }

  response = {
    sucesso : true
    checkins: $checkins
  }

  guid = "conectahr-metas-checkins-get-0001"
}
