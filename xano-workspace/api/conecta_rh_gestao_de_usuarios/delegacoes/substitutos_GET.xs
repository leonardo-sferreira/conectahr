// Substitutos que o Gestor pode escolher numa delegacao (change backend-gestor-pendencias, D3): pessoas ativas com
// conta do proprio setor e os outros Gestores ativos, so com nome e setor. Gestor, RH e Admin.
query "delegacoes/substitutos" verb=GET {
  api_group = "ConectaRH — Gestão de Usuários"
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

    precondition (($perfil_autenticado == "GESTOR") || ($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente Gestor, RH e Admin criam delegacoes."
    }

    var $titular_catalogo_id {
      value = $usuario_autenticado.id
    }

    // Catalogo de substitutos (change backend-gestor-pendencias, D3): pessoas ativas com conta do setor do titular e os
    // outros Gestores ativos. Nunca o proprio titular.
    db.get colaborador {
      field_name = "user_id"
      field_value = $titular_catalogo_id
      output = ["id", "departamento_id"]
    } as $ficha_titular_catalogo

    var $setor_titular {
      value = ($ficha_titular_catalogo != null) ? $ficha_titular_catalogo.departamento_id : null
    }

    db.query user {
      where = $db.user.ativo == true
      return = {type: "list"}
      output = ["id", "nome", "perfil"]
    } as $contas_ativas

    db.query colaborador {
      where = $db.colaborador.user_id != null
      return = {type: "list"}
      output = ["id", "user_id", "departamento_id", "status"]
    } as $fichas_com_conta

    db.query departamento {
      return = {type: "list"}
      output = ["id", "nome"]
    } as $setores

    var $catalogo {
      value = []
    }

    var $catalogo_ids {
      value = ","
    }

    foreach ($contas_ativas) {
      each as $conta {
        conditional {
          if ($conta.id != $titular_catalogo_id) {
            var $ficha_conta {
              value = null
            }

            foreach ($fichas_com_conta) {
              each as $fc {
                conditional {
                  if ($fc.user_id == $conta.id) {
                    var.update $ficha_conta {
                      value = $fc
                    }
                  }
                }
              }
            }

            var $mesmo_setor {
              value = ($ficha_conta != null) && ($setor_titular != null) && ($ficha_conta.departamento_id == $setor_titular) && ($ficha_conta.status != "Desligado")
            }

            var $e_gestor {
              value = ($conta.perfil|trim|to_upper) == "GESTOR"
            }

            conditional {
              if ($mesmo_setor || $e_gestor) {
                var $nome_setor {
                  value = null
                }

                foreach ($setores) {
                  each as $st {
                    conditional {
                      if (($ficha_conta != null) && ($st.id == $ficha_conta.departamento_id)) {
                        var.update $nome_setor {
                          value = $st.nome
                        }
                      }
                    }
                  }
                }

                var $motivo_catalogo {
                  value = $mesmo_setor ? "mesmo_setor" : "gestor"
                }

                var.update $catalogo {
                  value = $catalogo|push:{user_id: $conta.id, nome: $conta.nome, setor: $nome_setor, motivo: $motivo_catalogo}
                }

                var.update $catalogo_ids {
                  value = $catalogo_ids ~ ($conta.id|to_text) ~ ","
                }
              }
            }
          }
        }
      }
    }


    var $escopos_permitidos {
      value = "ferias,ausencia,documento,desligamento,correcao_ponto,solicitacao_rh,todas"|split:","
    }

    conditional {
      if (($perfil_autenticado != "RH") && ($perfil_autenticado != "ADMIN")) {
        var.update $escopos_permitidos {
          value = "ferias,correcao_ponto,todas"|split:","
        }
      }
    }
  }

  response = {
    sucesso     : true
    escopos     : $escopos_permitidos
    substitutos : $catalogo
  }

  guid = "conectahr-delegacoes-substitutos-get-0001"
}
