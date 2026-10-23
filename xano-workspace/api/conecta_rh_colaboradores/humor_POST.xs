// Responde o termometro de humor do ciclo de hoje (change termometro-de-humor, D3): nota de 1 (muito mal) a 5
// (muito bem) e, opcional, o que mais pesou (lista fechada). Uma vez por ciclo de 10 dias. Grava primeiro a
// participacao (a chave unica barra a segunda resposta) e depois so soma nos contadores anonimos do (ciclo, setor,
// nota) e do (ciclo, setor, motivo): nenhuma linha liga a pessoa a nota. Sem auditoria individual, de proposito
// (guardaria quem respondeu e quando, perto da nota). Qualquer perfil com ficha, nao desligado.
query "humor" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int nota
    text? motivo? filters=trim|lower
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

    precondition ($colaborador_autenticado.status != "Desligado") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao responde o termometro."
    }

    precondition (($input.nota >= 1) && ($input.nota <= 5)) {
      error_type = "inputerror"
      error = "A nota vai de 1 (muito mal) a 5 (muito bem)."
    }

    var $motivo_final {
      value = (($input.motivo == null) || ($input.motivo == "")) ? "" : $input.motivo
    }

    var $motivo_agulha {
      value = "," ~ $motivo_final ~ ","
    }

    precondition (($motivo_final == "") || (",carga_trabalho,reconhecimento,lideranca,colegas,comunicacao,estrutura,"|contains:$motivo_agulha)) {
      error_type = "inputerror"
      error = "Motivo invalido."
    }

    var $ano {
      value = ($hoje|substr:0:4)|to_int
    }

    var $mes {
      value = ($hoje|substr:5:2)|to_int
    }

    var $dia {
      value = ($hoje|substr:8:2)|to_int
    }

    var $a_jd {
      value = ((14 - $mes) / 12)|floor
    }

    var $y_jd {
      value = $ano + 4800 - $a_jd
    }

    var $m_jd {
      value = $mes + (12 * $a_jd) - 3
    }

    var $parte_mes {
      value = (((153 * $m_jd) + 2) / 5)|floor
    }

    var $bissextos {
      value = (($y_jd / 4)|floor) - (($y_jd / 100)|floor) + (($y_jd / 400)|floor)
    }

    var $dia_juliano {
      value = $dia + $parte_mes + (365 * $y_jd) + $bissextos - 32045
    }

    var $ciclo {
      value = (($dia_juliano - 2461335) / 10)|floor
    }

    db.query humor_participacao {
      where = $db.humor_participacao.ciclo == $ciclo && $db.humor_participacao.colaborador_id == $colaborador_autenticado.id
      return = {type: "single"}
    } as $ja_respondeu

    precondition ($ja_respondeu == null) {
      error_type = "inputerror"
      error = "Voce ja respondeu o termometro deste ciclo. O proximo abre em 10 dias."
    }

    db.add humor_participacao {
      data = {
        ciclo         : $ciclo
        colaborador_id: $colaborador_autenticado.id
      }
    } as $participacao

    var $departamento {
      value = ($colaborador_autenticado.departamento_id == null) ? 0 : $colaborador_autenticado.departamento_id
    }

    db.query humor_contagem {
      where = $db.humor_contagem.ciclo == $ciclo && $db.humor_contagem.departamento_id == $departamento && $db.humor_contagem.nota == $input.nota
      return = {type: "single"}
    } as $contagem

    conditional {
      if ($contagem == null) {
        db.add humor_contagem {
          data = {
            ciclo          : $ciclo
            departamento_id: $departamento
            nota           : $input.nota
            quantidade     : 1
          }
        } as $contagem_nova
      }

      else {
        db.edit humor_contagem {
          field_name = "id"
          field_value = $contagem.id
          data = {
            quantidade: $contagem.quantidade + 1
          }
        } as $contagem_editada
      }
    }

    conditional {
      if ($motivo_final != "") {
        db.query humor_motivo_contagem {
          where = $db.humor_motivo_contagem.ciclo == $ciclo && $db.humor_motivo_contagem.departamento_id == $departamento && $db.humor_motivo_contagem.motivo == $motivo_final
          return = {type: "single"}
        } as $motivo_contagem

        conditional {
          if ($motivo_contagem == null) {
            db.add humor_motivo_contagem {
              data = {
                ciclo          : $ciclo
                departamento_id: $departamento
                motivo         : $motivo_final
                quantidade     : 1
              }
            } as $motivo_novo
          }

          else {
            db.edit humor_motivo_contagem {
              field_name = "id"
              field_value = $motivo_contagem.id
              data = {
                quantidade: $motivo_contagem.quantidade + 1
              }
            } as $motivo_editado
          }
        }
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Obrigado! Sua resposta entrou no termometro deste ciclo."
    ciclo   : $ciclo
  }

  guid = "conectahr-humor-post-0001"
}
