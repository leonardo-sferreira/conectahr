// Feedback numa etapa enviada do formulario de metas (change ciclo-de-metas, D4). So o superior
// direto ou o gestor do departamento da pessoa, nunca no proprio formulario; so inclusao. Avisa a
// pessoa no sino. Auditado sem o texto.
query "formularios_meta/{id}/feedback" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int etapa
    text texto filters=trim|min:5|max:2000
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

    var $meu_colaborador_id {
      value = ($colaborador_autenticado != null ? $colaborador_autenticado.id : 0)
    }

    var $e_rh {
      value = (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN"))
    }

    db.get formulario_meta {
      field_name = "id"
      field_value = $input.id
    } as $form

    var $alvo {
      value = null
    }

    var $gestor_do_departamento_id {
      value = null
    }

    conditional {
      if ($form != null) {
        db.get colaborador {
          field_name = "id"
          field_value = $form.colaborador_id
          output = ["id", "nome", "user_id", "departamento_id", "superior_colaborador_id"]
        } as $colaborador_do_form

        var.update $alvo {
          value = $colaborador_do_form
        }

        conditional {
          if (($colaborador_do_form != null) && ($colaborador_do_form.departamento_id != null)) {
            db.get departamento {
              field_name = "id"
              field_value = $colaborador_do_form.departamento_id
              output = ["id", "nome", "gestor_colaborador_id"]
            } as $departamento_do_form

            var.update $gestor_do_departamento_id {
              value = ($departamento_do_form != null ? $departamento_do_form.gestor_colaborador_id : null)
            }
          }
        }
      }
    }

    var $e_o_proprio {
      value = (($alvo != null) && ($alvo.user_id == $usuario_autenticado.id))
    }

    var $pode_dar_feedback {
      value = (($alvo != null) && ($meu_colaborador_id != 0) && ($alvo.id != $meu_colaborador_id) && (($alvo.superior_colaborador_id == $meu_colaborador_id) || ($gestor_do_departamento_id == $meu_colaborador_id)))
    }

    precondition (($form != null) && $pode_dar_feedback) {
      error_type = "accessdenied"
      error = "Somente o superior direto ou o gestor do departamento da pessoa podem dar feedback."
    }

    precondition (($input.etapa >= 1) && ($input.etapa <= 3)) {
      error_type = "inputerror"
      error = "Etapa invalida. Use 1, 2 ou 3."
    }

    precondition ((($input.etapa == 1) && ($form.etapa1_enviada_em != null)) || (($input.etapa == 2) && ($form.etapa2_enviada_em != null)) || (($input.etapa == 3) && ($form.etapa3_enviada_em != null))) {
      error_type = "inputerror"
      error = "Esta etapa ainda nao foi enviada pela pessoa."
    }

    db.add feedback_meta {
      data = {formulario_meta_id: $form.id, etapa: $input.etapa, autor_user_id: $usuario_autenticado.id, texto: $input.texto}
    } as $feedback_criado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "registrar_feedback_meta"
        recurso    : "formulario_meta"
        registro_id: $form.id
        valor_novo : ("etapa=" ~ ($input.etapa|to_text) ~ "; feedback=" ~ ($feedback_criado.id|to_text))
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    function.run "ConectaHR/notificar" {
      input = {colaborador_id: $alvo.id, autor_user_id: $usuario_autenticado.id, tipo: "avaliacao_disponivel", titulo: "Novo feedback nas suas metas", mensagem: $usuario_autenticado.nome ~ " deixou um feedback na etapa " ~ ($input.etapa|to_text) ~ " das suas metas.", recurso: "formulario_meta", registro_id: $form.id}
    } as $aviso_pessoa
  }

  response = {
    sucesso : true
    mensagem: "Feedback registrado."
    feedback: $feedback_criado
  }

  guid = "conectahr-formularios-meta-feedback-post-0001"
}
