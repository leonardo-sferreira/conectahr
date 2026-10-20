// Envia a etapa aberta do formulario de metas (change ciclo-de-metas, D3): exige todas as
// perguntas preenchidas (e a autoavaliacao nas etapas 2 e 3) e, depois, nada muda. Avisa o
// superior direto (ou, sem ele, o gestor do departamento). Auditado.
query "meu_ciclo_metas/{ciclo_id}/enviar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int ciclo_id
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.get ciclo_metas {
      field_name = "id"
      field_value = $input.ciclo_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de metas nao encontrado."
    }

    var $etapa_aberta {
      value = null
    }

    conditional {
      if (($ciclo.etapa1_inicio <= $hoje) && ($hoje <= $ciclo.etapa1_fim)) {
        var.update $etapa_aberta {
          value = 1
        }
      }
    }

    conditional {
      if (($ciclo.etapa2_inicio <= $hoje) && ($hoje <= $ciclo.etapa2_fim)) {
        var.update $etapa_aberta {
          value = 2
        }
      }
    }

    conditional {
      if (($ciclo.etapa3_inicio <= $hoje) && ($hoje <= $ciclo.etapa3_fim)) {
        var.update $etapa_aberta {
          value = 3
        }
      }
    }

    precondition ($etapa_aberta != null) {
      error_type = "inputerror"
      error = "Nenhuma etapa deste ciclo esta aberta agora: fora da janela, as respostas nao mudam."
    }

    db.query formulario_meta {
      where = $db.formulario_meta.ciclo_metas_id == $ciclo.id && $db.formulario_meta.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $form

    precondition (($form != null) || ($etapa_aberta == 1)) {
      error_type = "inputerror"
      error = "Voce nao enviou as metas na etapa 1, entao nao ha o que acompanhar nesta etapa."
    }

    precondition ($form != null) {
      error_type = "inputerror"
      error = "Responda as perguntas antes de enviar."
    }

    precondition ((($etapa_aberta != 1) || ($form.etapa1_enviada_em == null)) && (($etapa_aberta != 2) || ($form.etapa2_enviada_em == null)) && (($etapa_aberta != 3) || ($form.etapa3_enviada_em == null))) {
      error_type = "inputerror"
      error = "Esta etapa ja foi enviada e nao pode mais mudar."
    }

    precondition (($etapa_aberta == 1) || ($form.etapa1_enviada_em != null)) {
      error_type = "inputerror"
      error = "Voce nao enviou as metas na etapa 1, entao nao ha o que acompanhar nesta etapa."
    }

    db.query resposta_meta {
      where = $db.resposta_meta.formulario_meta_id == $form.id
      return = {type: "list"}
    } as $respostas

    db.query pergunta_meta {
      where = $db.pergunta_meta.ativa == true
      return = {type: "list"}
      output = ["id"]
    } as $perguntas_ativas

    var $faltando {
      value = 0
    }

    foreach ($respostas) {
      each as $r {
        conditional {
          if (($etapa_aberta == 1) && (($r.meta == null) || ($r.meta == ""))) {
            var.update $faltando {
              value = $faltando + 1
            }
          }
        }

        conditional {
          if (($etapa_aberta == 2) && (($r.alcancado_etapa2 == null) || ($r.alcancado_etapa2 == "") || ($r.autoavaliacao_etapa2 == null))) {
            var.update $faltando {
              value = $faltando + 1
            }
          }
        }

        conditional {
          if (($etapa_aberta == 3) && (($r.alcancado_etapa3 == null) || ($r.alcancado_etapa3 == "") || ($r.autoavaliacao_etapa3 == null))) {
            var.update $faltando {
              value = $faltando + 1
            }
          }
        }
      }
    }

    precondition ((($respostas|count) > 0) && (($etapa_aberta != 1) || (($respostas|count) >= ($perguntas_ativas|count)))) {
      error_type = "inputerror"
      error = "Responda todas as perguntas antes de enviar."
    }

    precondition ($faltando == 0) {
      error_type = "inputerror"
      error = "Preencha todas as perguntas desta etapa (e a autoavaliacao, nas etapas 2 e 3) antes de enviar."
    }

    conditional {
      if ($etapa_aberta == 1) {
        db.edit formulario_meta {
          field_name = "id"
          field_value = $form.id
          data = {etapa1_enviada_em: "now", updated_at: "now"}
        } as $form_etapa1
      }
    }

    conditional {
      if ($etapa_aberta == 2) {
        db.edit formulario_meta {
          field_name = "id"
          field_value = $form.id
          data = {etapa2_enviada_em: "now", updated_at: "now"}
        } as $form_etapa2
      }
    }

    conditional {
      if ($etapa_aberta == 3) {
        db.edit formulario_meta {
          field_name = "id"
          field_value = $form.id
          data = {etapa3_enviada_em: "now", updated_at: "now"}
        } as $form_etapa3
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "enviar_etapa_meta"
        recurso    : "formulario_meta"
        registro_id: $form.id
        valor_novo : ("etapa=" ~ ($etapa_aberta|to_text))
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    // Avisa o superior direto; sem ele, o gestor do departamento.
    var $avisar_colaborador_id {
      value = $colaborador_autenticado.superior_colaborador_id
    }

    conditional {
      if (($avisar_colaborador_id == null) && ($colaborador_autenticado.departamento_id != null)) {
        db.get departamento {
          field_name = "id"
          field_value = $colaborador_autenticado.departamento_id
        } as $departamento_da_pessoa

        var.update $avisar_colaborador_id {
          value = ($departamento_da_pessoa != null ? $departamento_da_pessoa.gestor_colaborador_id : null)
        }
      }
    }

    conditional {
      if (($avisar_colaborador_id != null) && ($avisar_colaborador_id != $colaborador_autenticado.id)) {
        function.run "ConectaHR/notificar" {
          input = {colaborador_id: $avisar_colaborador_id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_novo", titulo: "Metas enviadas", mensagem: $colaborador_autenticado.nome ~ " enviou a etapa " ~ ($etapa_aberta|to_text) ~ " do ciclo de metas " ~ ($ciclo.ano|to_text) ~ ".", recurso: "formulario_meta", registro_id: $form.id}
        } as $aviso_superior
      }
    }
  }

  response = {
    sucesso      : true
    mensagem     : "Etapa enviada."
    formulario_id: $form.id
    etapa        : $etapa_aberta
  }

  guid = "conectahr-meu-ciclo-metas-enviar-post-0001"
}
