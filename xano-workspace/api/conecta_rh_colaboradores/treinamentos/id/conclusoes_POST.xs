// Registra a conclusao de um treinamento para varias pessoas de uma vez, uma turma (change
// treinamentos-obrigatorios, D3). A data nao pode ser futura; a validade e a data mais validade_meses (sem
// validade, nula; dias 29 a 31 viram 28 no mes de destino). Pessoa desligada ou repetida no mesmo dia e pulada.
// Cada pessoa recebe um aviso no sino. Auditado (uma linha por turma, com a quantidade). So RH e Admin.
query "treinamentos/{id}/conclusoes" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    json colaborador_ids
    date concluido_em
    text? instrutor? filters=trim|max:150
    text? certificado_url? filters=trim|max:500
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

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.get treinamento {
      field_name = "id"
      field_value = $input.id
    } as $treinamento

    precondition (($treinamento != null) && ($treinamento.ativo == true)) {
      error_type = "notfound"
      error = "Treinamento nao encontrado ou inativo."
    }

    var $data_texto {
      value = $input.concluido_em|format_timestamp:"Y-m-d":"UTC"
    }

    precondition ($data_texto <= $hoje) {
      error_type = "inputerror"
      error = "A data de conclusao nao pode ser no futuro."
    }

    precondition (($input.colaborador_ids|count) > 0) {
      error_type = "inputerror"
      error = "Escolha quem concluiu."
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

    var $registradas {
      value = 0
    }

    var $puladas {
      value = 0
    }

    foreach ($input.colaborador_ids) {
      each as $colaborador_id {
        db.get colaborador {
          field_name = "id"
          field_value = $colaborador_id
          output = ["id", "status", "user_id"]
        } as $pessoa

        db.query treinamento_conclusao {
          where = $db.treinamento_conclusao.treinamento_id == $treinamento.id && $db.treinamento_conclusao.colaborador_id == $colaborador_id && $db.treinamento_conclusao.concluido_em == $input.concluido_em
          return = {type: "single"}
        } as $repetida

        conditional {
          if (($pessoa == null) || ($pessoa.status == "Desligado") || ($repetida != null)) {
            var.update $puladas {
              value = $puladas + 1
            }
          }

          else {
            db.add treinamento_conclusao {
              data = {
                treinamento_id        : $treinamento.id
                colaborador_id        : $pessoa.id
                concluido_em          : $input.concluido_em
                valido_ate            : $valido_ate
                instrutor             : $input.instrutor
                certificado_url       : $input.certificado_url
                registrado_por_user_id: $usuario_autenticado.id
              }
            } as $conclusao

            var.update $registradas {
              value = $registradas + 1
            }

            function.run "ConectaHR/notificar" {
              input = {colaborador_id: $pessoa.id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_decidido", titulo: "Treinamento registrado", mensagem: "O RH registrou que você concluiu " ~ $treinamento.nome ~ ". Veja em Meus treinamentos.", recurso: "treinamento", registro_id: $treinamento.id}
            } as $aviso_pessoa
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "registrar_conclusao_treinamento"
        recurso      : "treinamento"
        registro_id  : $treinamento.id
        resultado    : "sucesso"
        justificativa: ($registradas|to_text) ~ " registradas, " ~ ($puladas|to_text) ~ " puladas"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    registradas: $registradas
    puladas    : $puladas
    valido_ate : $valido_ate
  }

  guid = "conectahr-treinamentos-conclusoes-post-0001"
}
