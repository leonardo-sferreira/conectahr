// SLA de solicitacoes (change sla-de-solicitacoes, D4): os 10 tipos com o setor responsavel, as horas uteis
// vigentes (72 quando nao ha linha ativa: "padrao"), quem alterou e quando. Admin, RH e Gestor leem.
query sla_config verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition (($perfil_autenticado == "ADMIN") || ($perfil_autenticado == "RH") || ($perfil_autenticado == "GESTOR")) {
      error_type = "accessdenied"
      error = "Somente Admin, RH e Gestor veem o SLA de solicitacoes."
    }

    db.query sla_config {
      return = {type: "list"}
    } as $configs

    var $tipos {
      value = "alteracao_cadastral,declaracao,documento_avulso,outra,privacidade_lgpd,desligamento,ferias,ausencia,correcao_ponto,acesso"|split:","
    }

    var $lista {
      value = []
    }

    foreach ($tipos) {
      each as $tipo_item {
        var $setor_item {
          value = "rh"
        }

        conditional {
          if (($tipo_item == "ferias") || ($tipo_item == "correcao_ponto")) {
            var.update $setor_item {
              value = "gestor"
            }
          }

          elseif ($tipo_item == "acesso") {
            var.update $setor_item {
              value = "admin"
            }
          }
        }

        var $linha {
          value = null
        }

        foreach ($configs) {
          each as $c {
            conditional {
              if (($c.tipo_solicitacao == $tipo_item) && ($c.setor == $setor_item)) {
                var.update $linha {
                  value = $c
                }
              }
            }
          }
        }

        var $quem {
          value = null
        }

        conditional {
          if (($linha != null) && ($linha.atualizado_por_user_id != null)) {
            db.get user {
              field_name = "id"
              field_value = $linha.atualizado_por_user_id
              output = ["id", "nome"]
            } as $autor

            var.update $quem {
              value = ($autor != null) ? $autor.nome : null
            }
          }
        }

        var $vigente {
          value = (($linha != null) && ($linha.ativo == true)) ? $linha.horas_uteis : 72
        }

        var $padrao {
          value = (($linha == null) || ($linha.ativo == false))
        }

        var $id_linha {
          value = ($linha != null) ? $linha.id : null
        }

        var $atualizado {
          value = ($linha != null) ? $linha.updated_at : null
        }

        var.update $lista {
          value = $lista|push:{id: $id_linha, tipo_solicitacao: $tipo_item, setor: $setor_item, horas_uteis: $vigente, padrao: $padrao, atualizado_por: $quem, atualizado_em: $atualizado}
        }
      }
    }
  }

  response = {
    sucesso     : true
    padrao_horas: 72
    pode_editar : ($perfil_autenticado == "ADMIN")
    slas        : $lista
  }

  guid = "conectahr-sla-config-get-0001"
}
