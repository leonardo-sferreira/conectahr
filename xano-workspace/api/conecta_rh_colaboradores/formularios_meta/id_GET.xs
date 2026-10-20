// Um formulario de metas com as respostas e os feedbacks de cada etapa (change ciclo-de-metas, D5).
// Veem: a propria pessoa, o RH, o Admin, o superior direto e o gestor do departamento dela.
// Formulario inexistente e falta de permissao dao a mesma recusa. So leitura.
query "formularios_meta/{id}" verb=GET {
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

    precondition (($form != null) && ($e_rh || $e_o_proprio || $pode_dar_feedback)) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para ver este formulario."
    }

    db.get ciclo_metas {
      field_name = "id"
      field_value = $form.ciclo_metas_id
    } as $ciclo

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

    db.query resposta_meta {
      where = $db.resposta_meta.formulario_meta_id == $form.id
      sort = {resposta_meta.ordem: "asc"}
      return = {type: "list"}
    } as $respostas

    var $feedbacks_form {
      value = []
    }

    db.query feedback_meta {
      where = $db.feedback_meta.formulario_meta_id == $form.id
      sort = {feedback_meta.created_at: "asc"}
      return = {type: "list"}
    } as $feedbacks_brutos

    foreach ($feedbacks_brutos) {
      each as $f {
        db.get user {
          field_name = "id"
          field_value = $f.autor_user_id
          output = ["id", "nome"]
        } as $autor_feedback

        var.update $feedbacks_form {
          value = $feedbacks_form|push:{id: $f.id, etapa: $f.etapa, texto: $f.texto, created_at: $f.created_at, autor_nome: ($autor_feedback != null ? $autor_feedback.nome : null)}
        }
      }
    }

    var $departamento_nome {
      value = null
    }

    conditional {
      if ($alvo.departamento_id != null) {
        db.get departamento {
          field_name = "id"
          field_value = $alvo.departamento_id
          output = ["id", "nome"]
        } as $departamento_alvo

        var.update $departamento_nome {
          value = ($departamento_alvo != null ? $departamento_alvo.nome : null)
        }
      }
    }
  }

  response = {
    sucesso          : true
    hoje             : $hoje
    formulario       : $form
    colaborador_nome : $alvo.nome
    departamento     : $departamento_nome
    ciclo            : $ciclo
    etapa_aberta     : $etapa_aberta
    respostas        : $respostas
    feedbacks        : $feedbacks_form
    pode_dar_feedback: $pode_dar_feedback
  }

  guid = "conectahr-formularios-meta-id-get-0001"
}
