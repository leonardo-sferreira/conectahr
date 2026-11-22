// Marca a reuniao 1:1 agendada como realizada (com as anotacoes) ou cancelada (com o motivo)
// (concluir-metas-pdi-equipe, D4). So o gestor que agendou. Cancelar avisa o liderado no sino e por
// e-mail; realizada, so no sino (D5). Auditado.
query "reunioes_individuais/{id}/situacao" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text situacao filters=trim|lower
    text? acordos? filters=trim|max:2000
    text? motivo? filters=trim|max:500
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    db.get reuniao_individual {
      field_name = "id"
      field_value = $input.id
    } as $reuniao

    precondition (($reuniao != null) && ($reuniao.gestor_user_id == $usuario_autenticado.id)) {
      error_type = "notfound"
      error = "Reuniao nao encontrada."
    }

    precondition ($reuniao.situacao == "agendada") {
      error_type = "inputerror"
      error = "So uma reuniao agendada pode ser marcada como realizada ou cancelada."
    }

    precondition (($input.situacao == "realizada") || ($input.situacao == "cancelada")) {
      error_type = "inputerror"
      error = "Situacao invalida. Use realizada ou cancelada."
    }

    var $acordos_final {
      value = (($input.acordos == null) || ($input.acordos == "")) ? $reuniao.acordos : $input.acordos
    }

    var $motivo_final {
      value = (($input.motivo == null) || ($input.motivo == "")) ? null : $input.motivo
    }

    db.edit reuniao_individual {
      field_name = "id"
      field_value = $reuniao.id
      data = {
        situacao           : $input.situacao
        situacao_em        : "now"
        acordos            : $acordos_final
        motivo_cancelamento: (($input.situacao == "cancelada") ? $motivo_final : null)
        updated_at         : "now"
      }
    } as $reuniao_atualizada

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : (($input.situacao == "cancelada") ? "cancelar_reuniao_individual" : "concluir_reuniao_individual")
        recurso      : "reuniao_individual"
        registro_id  : $reuniao.id
        resultado    : "sucesso"
      }
    } as $evento_auditoria

    var $quando_texto {
      value = ($reuniao.data_reuniao|format_timestamp:"d/m/Y":"UTC") ~ (($reuniao.hora == null) ? "" : (" as " ~ $reuniao.hora))
    }

    function.run "ConectaHR/notificar" {
      input = {colaborador_id: $reuniao.colaborador_id, autor_user_id: $usuario_autenticado.id, tipo: "acompanhamento_equipe", titulo: (($input.situacao == "cancelada") ? "Reuniao 1:1 cancelada" : "Reuniao 1:1 realizada"), mensagem: $usuario_autenticado.nome ~ (($input.situacao == "cancelada") ? " cancelou a reuniao 1:1 de " : " registrou a reuniao 1:1 de ") ~ $quando_texto ~ ".", recurso: "reuniao_individual", registro_id: $reuniao.id}
    } as $aviso_reuniao

    conditional {
      if ($input.situacao == "cancelada") {
        db.get colaborador {
          field_name = "id"
          field_value = $reuniao.colaborador_id
        } as $liderado

        conditional {
          if (($liderado != null) && ($liderado.user_id != null)) {
            db.get user {
              field_name = "id"
              field_value = $liderado.user_id
            } as $usuario_alvo

            conditional {
              if (($usuario_alvo != null) && $usuario_alvo.ativo) {
                db.add email_outbox {
                  data = {
                    destinatario_email: $usuario_alvo.email
                    destinatario_nome : $usuario_alvo.nome
                    assunto           : "ConectaRH - Reuniao 1:1 cancelada"
                    corpo             : "Ola " ~ $usuario_alvo.nome ~ ",\n\n" ~ $usuario_autenticado.nome ~ " cancelou a reuniao 1:1 de " ~ $quando_texto ~ "." ~ (($motivo_final == null) ? "" : ("\n\nMotivo: " ~ $motivo_final)) ~ "\n\nEste e um aviso automatico."
                    chave_idempotencia: "reuniao_cancelada_" ~ ($reuniao.id|to_text)
                  }
                } as $email_cancelamento
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso: true
    reuniao: $reuniao_atualizada
  }

  guid = "conectahr-reunioes-individuais-situacao-post-0001"
}
