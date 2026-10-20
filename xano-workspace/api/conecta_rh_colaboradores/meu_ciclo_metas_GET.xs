// Ciclos de metas da pessoa autenticada (change ciclo-de-metas, D3 e D5): cada ciclo com as datas,
// a etapa aberta hoje, o formulario dela (respostas e feedbacks) e as perguntas ativas, para quem
// ainda nao comecou. Vale para qualquer perfil com ficha de colaborador. So leitura.
query "meu_ciclo_metas" verb=GET {
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

    db.query pergunta_meta {
      where = $db.pergunta_meta.ativa == true
      sort = {pergunta_meta.ordem: "asc"}
      return = {type: "list"}
      output = ["id", "texto", "orientacao", "ordem"]
    } as $perguntas_ativas

    db.query ciclo_metas {
      sort = {ciclo_metas.ano: "desc"}
      return = {type: "list"}
    } as $todos_ciclos

    var $ciclos {
      value = []
    }

    foreach ($todos_ciclos) {
      each as $c {
        var $etapa_ciclo {
          value = null
        }

        conditional {
          if (($c.etapa1_inicio <= $hoje) && ($hoje <= $c.etapa1_fim)) {
            var.update $etapa_ciclo {
              value = 1
            }
          }
        }

        conditional {
          if (($c.etapa2_inicio <= $hoje) && ($hoje <= $c.etapa2_fim)) {
            var.update $etapa_ciclo {
              value = 2
            }
          }
        }

        conditional {
          if (($c.etapa3_inicio <= $hoje) && ($hoje <= $c.etapa3_fim)) {
            var.update $etapa_ciclo {
              value = 3
            }
          }
        }

        db.query formulario_meta {
          where = $db.formulario_meta.ciclo_metas_id == $c.id && $db.formulario_meta.colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $form

        var $respostas_form {
          value = []
        }

        var $feedbacks_form {
          value = []
        }

        conditional {
          if ($form != null) {
            db.query resposta_meta {
              where = $db.resposta_meta.formulario_meta_id == $form.id
              sort = {resposta_meta.ordem: "asc"}
              return = {type: "list"}
            } as $respostas_brutas

            var.update $respostas_form {
              value = $respostas_brutas
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
          }
        }

        var.update $ciclos {
          value = $ciclos|push:{id: $c.id, ano: $c.ano, etapa1_inicio: $c.etapa1_inicio, etapa1_fim: $c.etapa1_fim, etapa2_inicio: $c.etapa2_inicio, etapa2_fim: $c.etapa2_fim, etapa3_inicio: $c.etapa3_inicio, etapa3_fim: $c.etapa3_fim, etapa_aberta: $etapa_ciclo, formulario_id: ($form != null ? $form.id : null), etapa1_enviada_em: ($form != null ? $form.etapa1_enviada_em : null), etapa2_enviada_em: ($form != null ? $form.etapa2_enviada_em : null), etapa3_enviada_em: ($form != null ? $form.etapa3_enviada_em : null), respostas: $respostas_form, feedbacks: $feedbacks_form}
        }
      }
    }
  }

  response = {
    sucesso         : true
    hoje            : $hoje
    perguntas_ativas: $perguntas_ativas
    ciclos          : $ciclos
  }

  guid = "conectahr-meu-ciclo-metas-get-0001"
}
