// Colaborador cria uma meta anual em um ciclo. RH/ADMIN podem criar em
// nome de qualquer colaborador; Gestor pode criar para colaboradores
// do proprio departamento.
query metas verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int? colaborador_id?
    int ciclo_avaliacao_id
    text titulo filters=trim|max:500
    text descricao filters=trim|max:500
    text indicador filters=trim|max:300
    decimal? valor_esperado?
    text? unidade_medida? filters=trim|max:50
    decimal peso filters=max:100
    date? data_prazo?
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    // Define o colaborador-alvo: o proprio autenticado, ou outro quando
    // RH/ADMIN/Gestor informar.
    var $colaborador_alvo_id {
      value = null
    }

    conditional {
      if ($input.colaborador_id == null || $input.colaborador_id == $colaborador_autenticado.id) {
        precondition ($colaborador_autenticado != null) {
          error_type = "notfound"
          error = "Nao existe um colaborador vinculado a esta conta."
        }

        var.update $colaborador_alvo_id {
          value = $colaborador_autenticado.id
        }
      }
    }

    conditional {
      if ($input.colaborador_id != null && $colaborador_autenticado != null && $input.colaborador_id != $colaborador_autenticado.id) {
        precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
          error_type = "accessdenied"
          error = "Somente RH, ADMIN ou Gestor podem criar metas para outro colaborador."
        }

        var.update $colaborador_alvo_id {
          value = $input.colaborador_id
        }
      }
    }

    conditional {
      if ($input.colaborador_id != null && $colaborador_autenticado == null) {
        precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
          error_type = "accessdenied"
          error = "Somente RH, ADMIN ou Gestor podem criar metas para outro colaborador."
        }

        var.update $colaborador_alvo_id {
          value = $input.colaborador_id
        }
      }
    }

    db.get colaborador {
      field_name = "id"
      field_value = $colaborador_alvo_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.ciclo_avaliacao_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    db.add meta_avaliacao {
      data = {
        ciclo_avaliacao_id  : $ciclo.id
        colaborador_id        : $colaborador_alvo.id
        titulo                   : $input.titulo
        descricao                   : $input.descricao
        indicador                      : $input.indicador
        valor_esperado                    : $input.valor_esperado
        unidade_medida                       : $input.unidade_medida
        peso                                    : $input.peso
        data_prazo                                 : $input.data_prazo
        progresso_percentual                          : 0
        status                                           : "planejada"
        criado_por_user_id                                  : $usuario_autenticado.id
        updated_at                                             : "now"
      }
    } as $meta_criada
  }

  response = {
    sucesso : true
    mensagem: "Meta criada com sucesso."
    meta    : $meta_criada
  }

  guid = "conectahr-metas-post-0001"
}
