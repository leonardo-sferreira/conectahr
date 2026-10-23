// Avisa quem decide um pedido novo da pessoa colaborador_id (parte 2 das notificacoes, 12/10/2026),
// pela mesma regra que o sistema usa para decidir:
//   quem = "superior": o superior direto; sem ele, o Gestor do departamento; sem nenhum, o RH;
//   quem = "rh": as contas RH ativas;
//   quem = "superior_e_rh": os dois (ex.: ausencia, que o RH decide e o superior acompanha).
// Quem fez o pedido (autor_user_id) nunca e avisado do proprio pedido; colaborador inexistente nao avisa
// ninguem. Durante uma delegacao ativa, o substituto tambem e avisado. Devolve quantos avisos criou.
function "ConectaHR/notificar_decisores" {
  input {
    int colaborador_id
    int? autor_user_id?
    text quem
    text tipo
    text titulo filters=trim|max:150
    text mensagem filters=trim|max:1000
    text recurso filters=trim|max:50
    int? registro_id?
  }

  stack {
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $pessoa

    var $destinatarios {
      value = []
    }

    // Superior direto; sem ele, o Gestor do departamento (que nao seja a propria pessoa).
    var $responsavel_user_id {
      value = null
    }

    conditional {
      if ($pessoa != null && ($input.quem == "superior" || $input.quem == "superior_e_rh")) {
        var $responsavel_colaborador_id {
          value = $pessoa.superior_colaborador_id
        }

        conditional {
          if ($responsavel_colaborador_id == null && $pessoa.departamento_id != null) {
            db.get departamento {
              field_name = "id"
              field_value = $pessoa.departamento_id
            } as $departamento_pessoa

            conditional {
              if ($departamento_pessoa != null && $departamento_pessoa.gestor_colaborador_id != $pessoa.id) {
                var.update $responsavel_colaborador_id {
                  value = $departamento_pessoa.gestor_colaborador_id
                }
              }
            }
          }
        }

        conditional {
          if ($responsavel_colaborador_id != null) {
            db.get colaborador {
              field_name = "id"
              field_value = $responsavel_colaborador_id
            } as $responsavel

            conditional {
              if ($responsavel != null && $responsavel.user_id != null && $responsavel.user_id != $input.autor_user_id) {
                var.update $responsavel_user_id {
                  value = $responsavel.user_id
                }

                var.update $destinatarios {
                  value = $destinatarios|push:$responsavel.user_id
                }
              }
            }
          }
        }
      }
    }

    // RH: sempre em "rh" e "superior_e_rh"; em "superior", so quando nao ha superior nem Gestor.
    conditional {
      if ($pessoa != null && ($input.quem == "rh" || $input.quem == "superior_e_rh" || ($input.quem == "superior" && $responsavel_user_id == null))) {
        db.query user {
          where = $db.user.perfil == "RH" && $db.user.ativo == true
          return = {type: "list"}
          output = ["id"]
        } as $contas_rh

        foreach ($contas_rh) {
          each as $conta_rh {
            conditional {
              if ($conta_rh.id != $input.autor_user_id && $conta_rh.id != $responsavel_user_id) {
                var.update $destinatarios {
                  value = $destinatarios|push:$conta_rh.id
                }
              }
            }
          }
        }
      }
    }

    // Substitutos com delegacao ativa de algum decisor, no escopo do pedido ou em "todas" (change
    // notificacoes-de-publicacao, D4). O escopo da delegacao usa o nome do recurso, menos desligamento.
    var $escopo_pedido {
      value = ($input.recurso == "solicitacao_desligamento") ? "desligamento" : $input.recurso
    }

    var $hoje_delegacao {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $com_substitutos {
      value = $destinatarios
    }

    // Quem ja esta na lista, como texto ",1,4,", para nao repetir ninguem.
    var $na_lista_texto {
      value = ","
    }

    foreach ($destinatarios) {
      each as $ja_id {
        var.update $na_lista_texto {
          value = $na_lista_texto ~ ($ja_id|to_text) ~ ","
        }
      }
    }

    foreach ($destinatarios) {
      each as $decisor_id {
        db.query delegacao_aprovacao {
          where = $db.delegacao_aprovacao.titular_user_id == $decisor_id && $db.delegacao_aprovacao.cancelada_em == null && $db.delegacao_aprovacao.data_inicio <= $hoje_delegacao && $db.delegacao_aprovacao.data_fim >= $hoje_delegacao
          return = {type: "list"}
          output = ["substituto_user_id", "escopo"]
        } as $delegacoes_ativas

        foreach ($delegacoes_ativas) {
          each as $delegacao {
            var $agulha_substituto {
              value = "," ~ ($delegacao.substituto_user_id|to_text) ~ ","
            }

            var $ja_na_lista {
              value = $na_lista_texto|contains:$agulha_substituto
            }

            conditional {
              if ((($delegacao.escopo == $escopo_pedido) || ($delegacao.escopo == "todas")) && ($delegacao.substituto_user_id != $input.autor_user_id) && ($ja_na_lista == false)) {
                var.update $com_substitutos {
                  value = $com_substitutos|push:$delegacao.substituto_user_id
                }

                var.update $na_lista_texto {
                  value = $na_lista_texto ~ ($delegacao.substituto_user_id|to_text) ~ ","
                }
              }
            }
          }
        }
      }
    }

    var.update $destinatarios {
      value = $com_substitutos
    }

    foreach ($destinatarios) {
      each as $destinatario_id {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $destinatario_id
            tipo                : $input.tipo
            titulo              : $input.titulo
            mensagem            : $input.mensagem
            recurso             : $input.recurso
            registro_id         : $input.registro_id
          }
        } as $aviso
      }
    }
  }

  response = $destinatarios|count

  tags = ["conectahr"]
  guid = "conectahr-notificar-decisores-0001"
}
