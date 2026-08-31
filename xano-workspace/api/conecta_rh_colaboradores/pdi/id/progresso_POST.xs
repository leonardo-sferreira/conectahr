// Atualiza o progresso de uma acao de PDI, com evidencia. O
// responsavel designado, o proprio colaborador, ou RH/ADMIN podem
// atualizar.
query "pdi/{id}/progresso" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    decimal progresso_percentual filters=min:0|max:100
    text? evidencia? filters=trim|max:2000
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

    db.get pdi {
      field_name = "id"
      field_value = $input.id
    } as $pdi_atual

    precondition ($pdi_atual != null) {
      error_type = "notfound"
      error = "Acao de PDI nao encontrada."
    }

    precondition ($pdi_atual.status != "concluido" && $pdi_atual.status != "cancelado") {
      error_type = "inputerror"
      error = "Nao e possivel atualizar progresso de PDI concluido ou cancelado."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $pdi_atual.colaborador_id
    } as $colaborador_do_pdi

    var $e_o_proprio {
      value = ($colaborador_do_pdi != null && $colaborador_do_pdi.user_id == $usuario_autenticado.id)
    }

    var $e_o_responsavel {
      value = ($pdi_atual.responsavel_user_id == $usuario_autenticado.id)
    }

    precondition ($e_o_proprio || $e_o_responsavel || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para atualizar esta acao de PDI."
    }

    // Conclui automaticamente quando o progresso atinge 100%.
    var $status_final {
      value = ($input.progresso_percentual >= 100 ? "concluido" : "em_andamento")
    }

    db.edit pdi {
      field_name = "id"
      field_value = $pdi_atual.id
      data = {
        progresso_percentual: $input.progresso_percentual
        evidencia            : $input.evidencia
        status               : $status_final
        updated_at           : "now"
      }
    } as $pdi_atualizado
  }

  response = {
    sucesso : true
    mensagem: "Progresso atualizado com sucesso."
    pdi     : $pdi_atualizado
  }

  guid = "conectahr-pdi-progresso-post-0001"
}
