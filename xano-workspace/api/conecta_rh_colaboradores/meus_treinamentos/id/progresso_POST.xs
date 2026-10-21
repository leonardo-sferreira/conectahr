// Guarda quanto a pessoa assistiu do video de um treinamento (change treinamento-em-video, D2). A tela manda os
// segundos realmente vistos (sem os trechos pulados) e a posicao. O progresso nunca diminui e nao passa da duracao
// gravada no treinamento. Plausibilidade: o primeiro registro tem no maximo 90 segundos e cada aumento cabe em 2x o
// tempo real desde o ultimo, mais 15 segundos; fora disso, recusa. Qualquer perfil com ficha.
query "meus_treinamentos/{id}/progresso" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int segundos_vistos
    int posicao
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

    db.get treinamento {
      field_name = "id"
      field_value = $input.id
    } as $treinamento

    precondition (($treinamento != null) && ($treinamento.ativo == true) && ($treinamento.video_drive_id != null) && ($treinamento.video_duracao > 0)) {
      error_type = "notfound"
      error = "Treinamento nao encontrado, inativo ou sem video."
    }

    db.query treinamento_progresso {
      where = $db.treinamento_progresso.treinamento_id == $treinamento.id && $db.treinamento_progresso.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $progresso

    precondition (($input.segundos_vistos >= 0) && ($input.posicao >= 0) && ($input.segundos_vistos <= ($treinamento.video_duracao + 2)) && ($input.posicao <= ($treinamento.video_duracao + 2))) {
      error_type = "inputerror"
      error = "Progresso invalido."
    }

    var $vistos {
      value = ($input.segundos_vistos > $treinamento.video_duracao) ? $treinamento.video_duracao : $input.segundos_vistos
    }

    conditional {
      if ($progresso == null) {
        precondition ($vistos <= 90) {
          error_type = "inputerror"
          error = "Progresso mais rapido que o video. Assista sem pular."
        }

        db.add treinamento_progresso {
          data = {
            treinamento_id : $treinamento.id
            colaborador_id : $colaborador_autenticado.id
            segundos_vistos: $vistos
            posicao        : $input.posicao
            atualizado_em  : "now"
          }
        } as $progresso_novo

        var.update $vistos {
          value = $progresso_novo.segundos_vistos
        }
      }

      else {
        var $incremento {
          value = $vistos - $progresso.segundos_vistos
        }

        // Aumento <= 2 x (agora - ultima atualizacao) + 15 s, ou seja, ultima + (aumento - 15) / 2 <= agora.
        var $segundos_minimos {
          value = (($incremento - 15) / 2)|floor
        }

        precondition (($incremento <= 15) || (($progresso.atualizado_em|add_secs_to_timestamp:$segundos_minimos) <= now)) {
          error_type = "inputerror"
          error = "Progresso mais rapido que o video. Assista sem pular."
        }

        var $vistos_final {
          value = ($incremento > 0) ? $vistos : $progresso.segundos_vistos
        }

        db.edit treinamento_progresso {
          field_name = "id"
          field_value = $progresso.id
          data = {
            segundos_vistos: $vistos_final
            posicao        : $input.posicao
            atualizado_em  : "now"
          }
        } as $progresso_editado

        var.update $vistos {
          value = $vistos_final
        }
      }
    }
  }

  response = {
    sucesso        : true
    segundos_vistos: $vistos
    duracao        : $treinamento.video_duracao
  }

  guid = "conectahr-meus-treinamentos-progresso-post-0001"
}
