// Consulta a trilha de auditoria (item 7.11). Exclusivo de RH/ADMIN.
// Tela Auditoria (Figma 225:6784; tarefas 34 e 35 de concluir-frontend-streamlit, 20/10/2026): os
// eventos dos ultimos `dias` (padrao 30, ate 366), os mais recentes primeiro, no maximo 300. Os
// filtros (todos opcionais) sao aplicados no laco: `||` entre parenteses no where nao filtrava
// direito neste workspace. A resposta traz as opcoes dos filtros (recursos, acoes e usuarios que
// aparecem na janela) e o nome de quem fez cada acao. Nunca expoe senha, token ou codigo de acesso —
// os proprios eventos de auditoria ja sao gravados sem esses valores em
// nenhum campo (registrar_evento_sensivel/db.add auditoria em todo o
// codebase grava so acao/recurso/registro_id/valores/justificativa/
// resultado, nunca segredos).
query auditoria verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text? recurso? filters=trim
    int? registro_id?
    int? user_id?
    text? acao? filters=trim
    text? resultado? filters=trim
    int? dias?
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar a trilha de auditoria."
    }

    var $dias {
      value = (($input.dias == null) || ($input.dias < 1)) ? 30 : (($input.dias > 366) ? 366 : $input.dias)
    }

    var $segundos_atras {
      value = 0 - ($dias * 86400)
    }

    var $inicio {
      value = now|add_secs_to_timestamp:$segundos_atras
    }

    db.query auditoria {
      where = $db.auditoria.created_at >= $inicio
      sort = {auditoria.created_at: "desc"}
      return = {type: "list"}
    } as $janela

    // Nomes de quem aparece na trilha (so nome e perfil).
    db.query user {
      return = {type: "list"}
      output = ["id", "nome", "perfil"]
    } as $usuarios

    var $eventos {
      value = []
    }

    var $recursos_txt {
      value = ","
    }

    var $acoes_txt {
      value = ","
    }

    var $usuarios_txt {
      value = ","
    }

    var $recursos {
      value = []
    }

    var $acoes {
      value = []
    }

    var $usuarios_na_janela {
      value = []
    }

    foreach ($janela) {
      each as $e {
        // Opcoes dos filtros: tudo o que aparece na janela.
        conditional {
          if (($e.recurso != null) && (($recursos_txt|contains:("," ~ $e.recurso ~ ",")) == false)) {
            var.update $recursos_txt {
              value = $recursos_txt ~ $e.recurso ~ ","
            }

            var.update $recursos {
              value = $recursos|push:$e.recurso
            }
          }
        }

        conditional {
          if (($e.acao != null) && (($acoes_txt|contains:("," ~ $e.acao ~ ",")) == false)) {
            var.update $acoes_txt {
              value = $acoes_txt ~ $e.acao ~ ","
            }

            var.update $acoes {
              value = $acoes|push:$e.acao
            }
          }
        }

        conditional {
          if (($e.user_id != null) && (($usuarios_txt|contains:("," ~ ($e.user_id|to_text) ~ ",")) == false)) {
            var.update $usuarios_txt {
              value = $usuarios_txt ~ ($e.user_id|to_text) ~ ","
            }

            var.update $usuarios_na_janela {
              value = $usuarios_na_janela|push:$e.user_id
            }
          }
        }

        var $passa {
          value = ((($input.recurso == null) || ($input.recurso == "") || ($e.recurso == $input.recurso)) && (($input.acao == null) || ($input.acao == "") || ($e.acao == $input.acao)) && (($input.resultado == null) || ($input.resultado == "") || ($e.resultado == $input.resultado)) && (($input.user_id == null) || ($e.user_id == $input.user_id)) && (($input.registro_id == null) || ($e.registro_id == $input.registro_id)))
        }

        conditional {
          if ($passa && (($eventos|count) < 300)) {
            var.update $eventos {
              value = $eventos|push:{id: $e.id, created_at: $e.created_at, user_id: $e.user_id, acao: $e.acao, recurso: $e.recurso, registro_id: $e.registro_id, valor_anterior: $e.valor_anterior, valor_novo: $e.valor_novo, justificativa: $e.justificativa, resultado: $e.resultado, endereco_ip: $e.endereco_ip}
            }
          }
        }
      }
    }
  }

  response = {
    sucesso           : true
    dias              : $dias
    total             : ($eventos|count)
    limite            : 300
    eventos           : $eventos
    recursos          : $recursos
    acoes             : $acoes
    usuarios_na_janela: $usuarios_na_janela
    usuarios          : $usuarios
  }

  guid = "conectahr-auditoria-get-0001"
}
