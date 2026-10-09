// Mural publico de reconhecimento: somente registros publicos e
// ativos (nao cancelados/moderados). Feedback privado nunca aparece
// aqui.
query "mural_reconhecimento" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    db.query reconhecimento {
      where = $db.reconhecimento.visibilidade == "publico" && $db.reconhecimento.status == "ativo"
      sort = {reconhecimento.created_at: "desc"}
      return = {type: "list"}
    } as $mural_completo

    // Preferencias de privacidade (LGPD): quem saiu do mural nao aparece para os
    // outros, mas continua vendo os proprios reconhecimentos e o RH/Admin veem tudo.
    // Sem linha, menores de 18 anos ficam ocultos por padrao.
    var $perfil_mural {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_consulta

    db.query preferencia_privacidade {
      return = {type: "list"}
      output = ["colaborador_id", "ocultar_mural"]
    } as $preferencias_privacidade

    var $ids_com_preferencia {
      value = ","
    }

    var $ids_ocultar_mural {
      value = ","
    }

    foreach ($preferencias_privacidade) {
      each as $preferencia_item {
        var.update $ids_com_preferencia {
          value = $ids_com_preferencia ~ ($preferencia_item.colaborador_id|to_text) ~ ","
        }

        conditional {
          if ($preferencia_item.ocultar_mural) {
            var.update $ids_ocultar_mural {
              value = $ids_ocultar_mural ~ ($preferencia_item.colaborador_id|to_text) ~ ","
            }
          }
        }
      }
    }

    var $mural {
      value = []
    }

    foreach ($mural_completo) {
      each as $reconhecimento_item {
        var $chave_mural {
          value = "," ~ ($reconhecimento_item.destinatario_colaborador_id|to_text) ~ ","
        }

        var $oculto_mural {
          value = ($ids_ocultar_mural|contains:$chave_mural)
        }

        conditional {
          if ($oculto_mural == false && ($ids_com_preferencia|contains:$chave_mural) == false) {
            db.get colaborador {
              field_name = "id"
              field_value = $reconhecimento_item.destinatario_colaborador_id
            } as $destinatario_mural

            function.run "ConectaHR/idade_em_anos" {
              input = {data_nascimento: ($destinatario_mural != null ? $destinatario_mural.data_nascimento : null)}
            } as $idade_destinatario

            conditional {
              if ($idade_destinatario != null && $idade_destinatario < 18) {
                var.update $oculto_mural {
                  value = true
                }
              }
            }
          }
        }

        var $pode_ver_mural {
          value = (($oculto_mural == false) || ($perfil_mural == "RH") || ($perfil_mural == "ADMIN") || ($colaborador_consulta != null && $colaborador_consulta.id == $reconhecimento_item.destinatario_colaborador_id))
        }

        conditional {
          if ($pode_ver_mural) {
            var.update $mural {
              value = $mural|push:$reconhecimento_item
            }
          }
        }
      }
    }
  }

  response = {
    sucesso: true
    mural  : $mural
  }

  guid = "conectahr-mural-reconhecimento-get-0001"
}
