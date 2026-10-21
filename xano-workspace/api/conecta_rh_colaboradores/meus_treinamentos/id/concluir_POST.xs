// A propria pessoa conclui um treinamento com video (change treinamento-em-video, D3), so depois de assistir o
// minimo pedido (video_percentual_minimo da duracao, contando o progresso gravado aqui, nao o que a tela diz).
// Registra a conclusao com a data de hoje e a validade do treinamento, como o RH faria; no mesmo dia, nao repete.
// Zera o progresso, para a renovacao pedir o video de novo. Auditado. Qualquer perfil com ficha.
query "meus_treinamentos/{id}/concluir" verb=POST {
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

    precondition (($progresso != null) && (($progresso.segundos_vistos * 100) >= ($treinamento.video_percentual_minimo * $treinamento.video_duracao))) {
      error_type = "accessdenied"
      error = "Assista o video ate o minimo pedido antes de concluir."
    }

    var $data_texto {
      value = $hoje
    }
    // Validade: soma os meses na data (ano e mes), com o dia limitado a 28.
    var $valido_ate {
      value = null
    }

    conditional {
      if ($treinamento.validade_meses > 0) {
        var $ano {
          value = ($data_texto|substr:0:4)|to_int
        }

        var $mes {
          value = ($data_texto|substr:5:2)|to_int
        }

        var $dia {
          value = ($data_texto|substr:8:2)|to_int
        }

        var $meses_totais {
          value = ($ano * 12) + ($mes - 1) + $treinamento.validade_meses
        }

        var $novo_ano {
          value = ($meses_totais / 12)|floor
        }

        var $novo_mes {
          value = ($meses_totais - ($novo_ano * 12)) + 1
        }

        var $novo_dia {
          value = ($dia > 28) ? 28 : $dia
        }

        var $mes_texto {
          value = ($novo_mes < 10) ? ("0" ~ ($novo_mes|to_text)) : ($novo_mes|to_text)
        }

        var $dia_texto {
          value = ($novo_dia < 10) ? ("0" ~ ($novo_dia|to_text)) : ($novo_dia|to_text)
        }

        var.update $valido_ate {
          value = ($novo_ano|to_text) ~ "-" ~ $mes_texto ~ "-" ~ $dia_texto
        }
      }
    }

    db.query treinamento_conclusao {
      where = $db.treinamento_conclusao.treinamento_id == $treinamento.id && $db.treinamento_conclusao.colaborador_id == $colaborador_autenticado.id && $db.treinamento_conclusao.concluido_em == $hoje
      return = {type: "single"}
    } as $repetida

    conditional {
      if ($repetida == null) {
        db.add treinamento_conclusao {
          data = {
            treinamento_id        : $treinamento.id
            colaborador_id        : $colaborador_autenticado.id
            concluido_em          : $hoje
            valido_ate            : $valido_ate
            instrutor             : "Video no ConectaRH"
            registrado_por_user_id: $usuario_autenticado.id
          }
        } as $conclusao

        db.add auditoria {
          data = {
            user_id    : $usuario_autenticado.id
            acao       : "concluir_treinamento_video"
            recurso    : "treinamento"
            registro_id: $treinamento.id
            resultado  : "sucesso"
          }
        } as $evento_auditoria
      }
    }

    db.edit treinamento_progresso {
      field_name = "id"
      field_value = $progresso.id
      data = {
        segundos_vistos: 0
        posicao        : 0
        atualizado_em  : "now"
      }
    } as $progresso_zerado
  }

  response = {
    sucesso   : true
    mensagem  : "Treinamento concluido."
    valido_ate: $valido_ate
  }

  guid = "conectahr-meus-treinamentos-concluir-post-0001"
}
