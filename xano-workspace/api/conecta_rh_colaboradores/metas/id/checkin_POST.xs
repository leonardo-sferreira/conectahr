// Registra um check-in de progresso na meta: percentual, comentario,
// dificuldades, evidencia e alteracao de prazo. Cada chamada cria um
// evento na trilha `meta_checkin` (historico completo, nunca sobrescrito)
// e atualiza o "ultimo check-in" em `meta_avaliacao` para consulta
// rapida. O proprio colaborador (dono da meta), o lider direto dele
// (concluir-metas-pdi-equipe, D3) ou RH/ADMIN podem registrar. Sempre em nome de quem
// registrou (registrado_por_user_id), na auditoria; o dono e avisado no sino.
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $id_ficha_autenticada {
      value = ($colaborador_autenticado == null) ? 0 : $colaborador_autenticado.id
    }

    var $superior_da_meta {
      value = ($colaborador_da_meta == null) ? null : $colaborador_da_meta.superior_colaborador_id
    }

    var $e_lider_direto {
      value = ($superior_da_meta != null) && ($superior_da_meta == $id_ficha_autenticada) && ($colaborador_da_meta.status != "Desligado")
    }

    precondition ($e_o_proprio || $e_lider_direto || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
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

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "registrar_checkin_meta"
        recurso    : "meta_avaliacao"
        registro_id: $meta_atual.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    conditional {
      if ($e_o_proprio == false) {
        function.run "ConectaHR/notificar" {
          input = {colaborador_id: $meta_atual.colaborador_id, autor_user_id: $usuario_autenticado.id, tipo: "acompanhamento_equipe", titulo: "Check-in na sua meta", mensagem: $usuario_autenticado.nome ~ " registrou " ~ ($input.progresso_percentual|to_text) ~ "% na meta \"" ~ $meta_atual.titulo ~ "\".", recurso: "meta_avaliacao", registro_id: $meta_atual.id}
        } as $aviso_checkin
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
