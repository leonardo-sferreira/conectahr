// Lista solicitacoes de correcao de ponto pendentes de decisao.
// RH/ADMIN veem todas; Gestor ve somente as do departamento que gerencia.
query correcoes_ponto verb=GET {
  api_group = "ConectaRH - Ponto"
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

    // Qualquer perfil: RH e Admin veem todas; os demais, so as da propria equipe (tarefa 83).

    db.query correcao_ponto {
      where = $db.correcao_ponto.status == "pendente"
      sort = {correcao_ponto.created_at: "asc"}
      return = {type: "list"}
    } as $correcoes_pendentes

    // Escopo do Gestor: departamento que ele gerencia (se houver).
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $departamento_escopo_id {
      value = null
    }

    conditional {
      if ($colaborador_autenticado != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerenciado

        conditional {
          if ($departamento_gerenciado != null) {
            var.update $departamento_escopo_id {
              value = $departamento_gerenciado.id
            }
          }
        }
      }
    }

    var $correcoes_no_escopo {
      value = []
    }

    // Delegacoes vigentes em que quem pede e o substituto (change backend-gestor-pendencias, D3), escopo "correcao_ponto" ou
    // "todas": os titulares, com a ficha e o setor que gerenciam, para incluir os pedidos que eles decidiriam.
    var $titulares_delegacao {
      value = []
    }

    var $hoje_delegacao_fila {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    db.query delegacao_aprovacao {
      where = $db.delegacao_aprovacao.substituto_user_id == $usuario_autenticado.id && $db.delegacao_aprovacao.cancelada_em == null && $db.delegacao_aprovacao.data_inicio <= $hoje_delegacao_fila && $db.delegacao_aprovacao.data_fim >= $hoje_delegacao_fila
      return = {type: "list"}
    } as $delegacoes_recebidas

    foreach ($delegacoes_recebidas) {
      each as $dr {
        conditional {
          if (($dr.escopo == "correcao_ponto") || ($dr.escopo == "todas")) {
            db.get colaborador {
              field_name = "user_id"
              field_value = $dr.titular_user_id
              output = ["id", "nome"]
            } as $ficha_titular_dr

            conditional {
              if ($ficha_titular_dr != null) {
                db.query departamento {
                  where = $db.departamento.gestor_colaborador_id == $ficha_titular_dr.id
                  return = {type: "single"}
                } as $setor_titular_dr

                var $setor_titular_dr_id {
                  value = ($setor_titular_dr != null) ? $setor_titular_dr.id : null
                }

                var.update $titulares_delegacao {
                  value = $titulares_delegacao|push:{colaborador_id: $ficha_titular_dr.id, setor_id: $setor_titular_dr_id, nome: $ficha_titular_dr.nome}
                }
              }
            }
          }
        }
      }
    }

    conditional {
      // Sem departamento gerenciado, o Gestor nao ve fila nenhuma (antes caia em "ve tudo").
      if ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
        var.update $correcoes_no_escopo {
          value = $correcoes_pendentes
        }
      }
    }

    // Gestor (tarefa 81): as correcoes de quem tem ele como superior direto e, de quem nao
    // tem superior, as do departamento que ele gerencia. Nunca as proprias.
    conditional {
      if ($perfil_autenticado != "RH" && $perfil_autenticado != "ADMIN" && $colaborador_autenticado != null) {
        foreach ($correcoes_pendentes) {
          each as $correcao_item {
            db.get colaborador {
              field_name = "id"
              field_value = $correcao_item.colaborador_id
            } as $colaborador_da_correcao

            var $no_escopo {
              value = ($colaborador_da_correcao != null && $colaborador_da_correcao.id != $colaborador_autenticado.id && ($colaborador_da_correcao.superior_colaborador_id == $colaborador_autenticado.id || ($colaborador_da_correcao.superior_colaborador_id == null && $departamento_escopo_id != null && $colaborador_da_correcao.departamento_id == $departamento_escopo_id)))
            }

            var $titular_da_correcao {
              value = null
            }

            conditional {
              if (($no_escopo == false) && ($colaborador_da_correcao != null) && ($colaborador_da_correcao.id != $colaborador_autenticado.id)) {
                foreach ($titulares_delegacao) {
                  each as $tc {
                    conditional {
                      if (($titular_da_correcao == null) && ($colaborador_da_correcao.id != $tc.colaborador_id) && (($colaborador_da_correcao.superior_colaborador_id == $tc.colaborador_id) || (($colaborador_da_correcao.superior_colaborador_id == null) && ($tc.setor_id != null) && ($colaborador_da_correcao.departamento_id == $tc.setor_id)))) {
                        var.update $titular_da_correcao {
                          value = $tc.nome
                        }
                      }
                    }
                  }
                }
              }
            }

            conditional {
              if ($no_escopo) {
                var.update $correcoes_no_escopo {
                  value = $correcoes_no_escopo|push:$correcao_item
                }
              }

              elseif ($titular_da_correcao != null) {
                var.update $correcoes_no_escopo {
                  value = $correcoes_no_escopo|push:($correcao_item|set:"delegado_de":$titular_da_correcao)
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso   : true
    correcoes : $correcoes_no_escopo
  }

  guid = "conectahr-correcoes-ponto-get-0001"
}
