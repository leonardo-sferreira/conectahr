// Lista os colaboradores nao desligados que fazem aniversario no mes corrente.
// Visivel para qualquer usuario autenticado (informacao social, sem
// dado sensivel): retorna apenas nome e dia/mes, nunca o ano de
// nascimento, para nao revelar idade.
query "colaboradores/aniversariantes" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuario autenticado.
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

    // Preferencias de privacidade (LGPD): quem saiu da lista nao aparece para os
    // outros. Sem linha, menores de 18 anos ficam ocultos por padrao.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_consulta

    db.query preferencia_privacidade {
      return = {type: "list"}
      output = ["colaborador_id", "ocultar_aniversario"]
    } as $preferencias_privacidade

    var $ids_com_preferencia {
      value = ","
    }

    var $ids_ocultar_aniversario {
      value = ","
    }

    foreach ($preferencias_privacidade) {
      each as $preferencia_item {
        var.update $ids_com_preferencia {
          value = $ids_com_preferencia ~ ($preferencia_item.colaborador_id|to_text) ~ ","
        }

        conditional {
          if ($preferencia_item.ocultar_aniversario) {
            var.update $ids_ocultar_aniversario {
              value = $ids_ocultar_aniversario ~ ($preferencia_item.colaborador_id|to_text) ~ ","
            }
          }
        }
      }
    }

    // Mes corrente, no formato de dois digitos (ex.: "08").
    var $mes_atual {
      value = now|format_timestamp:"m":"UTC"
    }

    // Colaboradores ativos com data de nascimento informada.
    db.query colaborador {
      where = $db.colaborador.status != "Desligado" && $db.colaborador.data_nascimento != null
      return = {type: "list"}
      output = ["id", "nome", "data_nascimento"]
    } as $candidatos

    var $aniversariantes {
      value = []
    }

    foreach ($candidatos) {
      each as $colaborador_item {
        var $mes_nascimento {
          value = $colaborador_item.data_nascimento|format_timestamp:"m":"UTC"
        }

        var $chave_aniversario {
          value = "," ~ ($colaborador_item.id|to_text) ~ ","
        }

        function.run "ConectaHR/idade_em_anos" {
          input = {data_nascimento: $colaborador_item.data_nascimento}
        } as $idade_aniversariante

        var $oculto_aniversario {
          value = (($ids_ocultar_aniversario|contains:$chave_aniversario) || (($ids_com_preferencia|contains:$chave_aniversario) == false && $idade_aniversariante != null && $idade_aniversariante < 18))
        }

        var $e_o_proprio_aniversario {
          value = ($colaborador_consulta != null && $colaborador_consulta.id == $colaborador_item.id)
        }

        conditional {
          if ($mes_nascimento == $mes_atual && ($oculto_aniversario == false || $e_o_proprio_aniversario)) {
            var.update $aniversariantes {
              value = $aniversariantes|push:{
                id        : $colaborador_item.id
                nome      : $colaborador_item.nome
                aniversario: ($colaborador_item.data_nascimento|format_timestamp:"d/m":"UTC")
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso       : true
    mes           : $mes_atual
    aniversariantes: $aniversariantes
  }

  guid = "conectahr-colaboradores-aniversariantes-get-0001"
}
