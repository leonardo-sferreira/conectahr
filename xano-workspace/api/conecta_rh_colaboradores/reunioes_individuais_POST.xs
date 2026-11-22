// Gestor agenda ou registra uma reuniao individual (1:1) com um liderado direto
// (concluir-metas-pdi-equipe, D4): data, hora, pauta (assuntos), anotacoes (acordos) e situacao
// (agendada ou realizada). Por padrao e privada (so gestor e colaborador); pode ser
// compartilhada com RH. Agendada avisa no sino e por e-mail; realizada, so no sino (D5).
query reunioes_individuais verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    date data_reuniao
    text assuntos filters=trim|max:2000
    text? acordos? filters=trim|max:2000
    text? acoes? filters=trim|max:2000
    int? responsavel_acoes_user_id?
    date? prazo_acoes?
    date? proxima_reuniao?
    text? visibilidade? filters=trim
    text? hora? filters=trim|max:5
    text? situacao? filters=trim|lower
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

    precondition ($perfil_autenticado == "GESTOR" || $perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente Gestor, RH ou ADMIN podem registrar reunioes individuais."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Gestor so pode registrar com colaboradores do proprio departamento.
    conditional {
      if ($perfil_autenticado == "GESTOR") {
        db.get colaborador {
          field_name = "user_id"
          field_value = $usuario_autenticado.id
        } as $colaborador_gestor

        precondition ($colaborador_gestor != null) {
          error_type = "notfound"
          error = "Nao existe um colaborador vinculado a esta conta."
        }

        precondition (($colaborador_alvo.superior_colaborador_id != null) && ($colaborador_alvo.superior_colaborador_id == $colaborador_gestor.id) && ($colaborador_alvo.status != "Desligado")) {
          error_type = "accessdenied"
          error = "Voce so pode registrar reunioes com os seus liderados diretos."
        }
      }
    }

    var $visibilidade_normalizada {
      value = "privado"
    }

    conditional {
      if ($input.visibilidade != null) {
        var.update $visibilidade_normalizada {
          value = $input.visibilidade|trim|to_lower
        }

        precondition ($visibilidade_normalizada == "privado" || $visibilidade_normalizada == "compartilhado_rh") {
          error_type = "inputerror"
          error = "Visibilidade invalida. Use privado ou compartilhado_rh."
        }
      }
    }

    var $situacao_final {
      value = (($input.situacao == null) || ($input.situacao == "")) ? "agendada" : $input.situacao
    }

    precondition (($situacao_final == "agendada") || ($situacao_final == "realizada")) {
      error_type = "inputerror"
      error = "Situacao invalida. Use agendada ou realizada."
    }

    var $hora_final {
      value = (($input.hora == null) || ($input.hora == "")) ? null : $input.hora
    }

    precondition (($hora_final == null) || ((($hora_final|strlen) == 5) && (($hora_final|substr:2:1) == ":") && ((($hora_final|substr:0:2)|to_int) <= 23) && ((($hora_final|substr:3:2)|to_int) <= 59))) {
      error_type = "inputerror"
      error = "Hora invalida. Use HH:MM."
    }

    db.add reuniao_individual {
      data = {
        colaborador_id             : $colaborador_alvo.id
        gestor_user_id                : $usuario_autenticado.id
        data_reuniao                     : $input.data_reuniao
        assuntos                            : $input.assuntos
        acordos                                : $input.acordos
        acoes                                     : $input.acoes
        responsavel_acoes_user_id                   : $input.responsavel_acoes_user_id
        prazo_acoes                                    : $input.prazo_acoes
        proxima_reuniao                                   : $input.proxima_reuniao
        visibilidade                                         : $visibilidade_normalizada
        hora                                                    : $hora_final
        situacao                                                : $situacao_final
        situacao_em                                             : "now"
        updated_at                                              : "now"
      }
    } as $reuniao_criada

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "registrar_reuniao_individual"
        recurso      : "reuniao_individual"
        registro_id  : $reuniao_criada.id
        justificativa: $situacao_final
        resultado    : "sucesso"
      }
    } as $evento_auditoria

    var $quando_texto {
      value = ($input.data_reuniao|format_timestamp:"d/m/Y":"UTC") ~ (($hora_final == null) ? "" : (" as " ~ $hora_final))
    }

    function.run "ConectaHR/notificar" {
      input = {colaborador_id: $colaborador_alvo.id, autor_user_id: $usuario_autenticado.id, tipo: "acompanhamento_equipe", titulo: (($situacao_final == "agendada") ? "Reuniao 1:1 agendada" : "Reuniao 1:1 registrada"), mensagem: $usuario_autenticado.nome ~ (($situacao_final == "agendada") ? " agendou uma reuniao 1:1 com voce em " : " registrou a reuniao 1:1 de ") ~ $quando_texto ~ ".", recurso: "reuniao_individual", registro_id: $reuniao_criada.id}
    } as $aviso_reuniao

    conditional {
      if (($situacao_final == "agendada") && ($colaborador_alvo.user_id != null)) {
        db.get user {
          field_name = "id"
          field_value = $colaborador_alvo.user_id
        } as $usuario_alvo

        conditional {
          if (($usuario_alvo != null) && $usuario_alvo.ativo) {
            db.add email_outbox {
              data = {
                destinatario_email: $usuario_alvo.email
                destinatario_nome : $usuario_alvo.nome
                assunto           : "ConectaRH - Reuniao 1:1 agendada"
                corpo             : "Ola " ~ $usuario_alvo.nome ~ ",\n\n" ~ $usuario_autenticado.nome ~ " agendou uma reuniao 1:1 com voce em " ~ $quando_texto ~ ".\n\nPauta: " ~ $input.assuntos ~ "\n\nVeja no ConectaRH, em Trajetoria.\n\nEste e um aviso automatico."
                chave_idempotencia: "reuniao_agendada_" ~ ($reuniao_criada.id|to_text)
              }
            } as $email_reuniao
          }
        }
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Reuniao registrada com sucesso."
    reuniao : $reuniao_criada
  }

  guid = "conectahr-reunioes-individuais-post-0001"
}
