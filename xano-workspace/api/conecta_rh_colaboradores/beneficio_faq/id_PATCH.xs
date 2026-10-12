// Edita uma pergunta da FAQ de um beneficio (tarefa 85). Somente RH ou Admin. Avisa quem tem o beneficio.
query "beneficio_faq/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text pergunta filters=trim|min:3|max:200
    text resposta filters=trim|min:3|max:2000
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.get beneficio_faq {
      field_name = "id"
      field_value = $input.id
    } as $faq

    precondition ($faq != null && $faq.ativo) {
      error_type = "notfound"
      error = "Pergunta nao encontrada."
    }

    db.get beneficio {
      field_name = "id"
      field_value = $faq.beneficio_id
    } as $beneficio

    db.edit beneficio_faq {
      field_name = "id"
      field_value = $faq.id
      data = {pergunta: $input.pergunta, resposta: $input.resposta, atualizado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
    } as $faq_atualizada

    db.query colaborador_beneficio {
      where = $db.colaborador_beneficio.beneficio_id == $beneficio.id && $db.colaborador_beneficio.ativo == true
      return = {type: "list"}
    } as $vinculos_do_beneficio

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $avisados {
      value = 0
    }

    foreach ($vinculos_do_beneficio) {
      each as $vinculo_aviso {
        conditional {
          if ($vinculo_aviso.data_fim == null || $vinculo_aviso.data_fim >= $hoje) {
            db.get colaborador {
              field_name = "id"
              field_value = $vinculo_aviso.colaborador_id
            } as $pessoa_aviso

            conditional {
              if ($pessoa_aviso != null && $pessoa_aviso.user_id != null) {
                db.add notificacao_interna {
                  data = {
                    destinatario_user_id: $pessoa_aviso.user_id
                    tipo                : "beneficio_atualizado"
                    titulo              : "Novidade no beneficio " ~ $beneficio.nome
                    mensagem            : "O RH atualizou a resposta sobre o beneficio " ~ $beneficio.nome ~ ": " ~ $input.pergunta
                    recurso             : "beneficio"
                    registro_id         : $vinculo_aviso.beneficio_id
                  }
                } as $aviso_beneficio
              }
            }

            var.update $avisados {
              value = $avisados + 1
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id     : $usuario_autenticado.id
        acao        : "editar_faq_beneficio"
        recurso     : "beneficio_faq"
        registro_id : $faq.id
        valor_antigo: $faq.pergunta
        valor_novo  : $input.pergunta
        resultado   : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    faq     : $faq_atualizada
    avisados: $avisados
  }

  guid = "conectahr-beneficio-faq-id-patch-0001"
}
