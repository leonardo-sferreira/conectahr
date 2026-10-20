// Avaliacoes de um ciclo de avaliacao de desempenho (change pesquisa-clima-e-avaliacao-360, D5): quem e
// avaliado (nome e departamento), quem avalia (nome), a relacao, a situacao, a nota e a data do envio.
// So RH e Admin. As respostas por competencia ficam no detalhe (`avaliacoes/{id}`).
query "ciclos_avaliacao/{id}/avaliacoes" verb=GET {
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

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    db.query avaliacao {
      where = $db.avaliacao.ciclo_avaliacao_id == $ciclo.id
      sort = {avaliacao.created_at: "asc"}
      return = {type: "list"}
    } as $avaliacoes_ciclo

    var $avaliacoes {
      value = []
    }

    foreach ($avaliacoes_ciclo) {
      each as $av {
        db.get colaborador {
          field_name = "id"
          field_value = $av.colaborador_id
          output = ["id", "nome", "departamento_id"]
        } as $avaliado

        var $departamento_nome {
          value = null
        }

        conditional {
          if (($avaliado != null) && ($avaliado.departamento_id != null)) {
            db.get departamento {
              field_name = "id"
              field_value = $avaliado.departamento_id
              output = ["id", "nome"]
            } as $dep_avaliado

            var.update $departamento_nome {
              value = ($dep_avaliado != null ? $dep_avaliado.nome : null)
            }
          }
        }

        db.get user {
          field_name = "id"
          field_value = $av.user_id
          output = ["id", "nome"]
        } as $avaliador

        var.update $avaliacoes {
          value = $avaliacoes|push:{
            id               : $av.id
            colaborador_id   : $av.colaborador_id
            avaliado_nome    : ($avaliado != null ? $avaliado.nome : null)
            departamento_id  : ($avaliado != null ? $avaliado.departamento_id : null)
            departamento     : $departamento_nome
            avaliador_nome   : ($avaliador != null ? $avaliador.nome : null)
            relacao_avaliador: $av.relacao_avaliador
            status           : $av.status
            nota             : $av.nota
            data_avaliacao   : $av.data_avaliacao
          }
        }
      }
    }
  }

  response = {
    sucesso   : true
    ciclo     : $ciclo
    avaliacoes: $avaliacoes
  }

  guid = "conectahr-ciclos-avaliacao-avaliacoes-get-0001"
}
