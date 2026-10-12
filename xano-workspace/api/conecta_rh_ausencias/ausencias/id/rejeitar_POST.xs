// Rejeita uma solicitacao de ausencia.
// RH, Admin, o superior direto da pessoa ou, sem superior, o gestor do departamento (tarefa 83).
// A justificativa da rejeicao e obrigatoria.
query "ausencias/{id}/rejeitar" verb=POST {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
    text observacao filters=trim|min:5|max:1000
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
  
    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem rejeitar.
    // Quem decide e conferido mais abaixo, pela hierarquia (tarefa 83).
  
    // Localiza a ausencia.
    db.get ausencia {
      field_name = "id"
      field_value = $input.id
    } as $ausencia_atual
  
    precondition ($ausencia_atual != null) {
      error_type = "notfound"
      error = "Ausencia nao encontrada."
    }

    // Bloqueio de autoaprovacao: ninguem decide uma solicitacao em que e o
    // proprio colaborador, nem RH/ADMIN. A tentativa e auditada antes da recusa.
    db.get colaborador {
      field_name = "user_id"
      field_value = $auth.id
    } as $colaborador_do_decisor

    conditional {
      if ($colaborador_do_decisor != null && $colaborador_do_decisor.id == $ausencia_atual.colaborador_id) {
        db.add auditoria {
          data = {
            user_id    : $auth.id
            acao       : "autoaprovacao_bloqueada"
            recurso    : "ausencia"
            registro_id: $ausencia_atual.id
            resultado  : "falha"
          }
        } as $evento_autoaprovacao

        precondition (false) {
          error_type = "accessdenied"
          error = "Voce nao pode decidir uma solicitacao propria."
        }
      }
    }
  
    // Somente ausencias Pendentes podem ser rejeitadas.
    var $status_atual {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_atual == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente ausencias com status Pendente podem ser rejeitadas."
    }
  
    // Confirma que o colaborador vinculado ainda existe.
    db.get colaborador {
      field_name = "id"
      field_value = $ausencia_atual.colaborador_id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador vinculado a ausencia nao encontrado."
    }

    // Hierarquia (tarefas 81 e 83): RH e Admin; o superior direto da pessoa; ou, se ela nao tem
    // superior, o gestor do departamento dela. Vale para qualquer perfil.
    var $pode_decidir_ausencia {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    conditional {
      if ($pode_decidir_ausencia == false && $colaborador_do_decisor != null && $colaborador.superior_colaborador_id != null) {
        var.update $pode_decidir_ausencia {
          value = ($colaborador.superior_colaborador_id == $colaborador_do_decisor.id)
        }
      }
    }

    conditional {
      if ($pode_decidir_ausencia == false && $colaborador_do_decisor != null && $colaborador.superior_colaborador_id == null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_do_decisor.id && $db.departamento.id == $colaborador.departamento_id
          return = {type: "single"}
        } as $departamento_do_decisor_pode_decidir_ausencia

        var.update $pode_decidir_ausencia {
          value = ($departamento_do_decisor_pode_decidir_ausencia != null)
        }
      }
    }

    precondition ($pode_decidir_ausencia) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para decidir esta ausencia."
    }
  
    // Rejeita a ausencia e registra a justificativa.
    // Diagnostico (codigo CID, ex.: J11 ou F32.1) nao deve ir na observacao: fica so
    // no atestado (LGPD, dado de saude). Sem regex (os filtros regex_* nao funcionam
    // neste workspace): separa o texto em palavras e confere letra + 2 digitos.
    var $observacao_tem_cid {
      value = false
    }

    conditional {
      if ($input.observacao != null) {
        var $observacao_normalizada {
          value = $input.observacao|to_upper|replace:",":" "|replace:";":" "|replace:":":" "|replace:"(":" "|replace:")":" "|replace:"[":" "|replace:"]":" "|replace:"/":" "|replace:"-":" "|replace:"_":" "|replace:"!":" "|replace:"?":" "
        }

        var $palavras_observacao {
          value = $observacao_normalizada|split:" "
        }

        foreach ($palavras_observacao) {
          each as $palavra {
            var $tamanho_palavra {
              value = $palavra|strlen
            }

            conditional {
              if ($tamanho_palavra >= 3) {
                var $cid_letra {
                  value = $palavra|substr:0:1
                }

                var $cid_digito_1 {
                  value = $palavra|substr:1:1
                }

                var $cid_digito_2 {
                  value = $palavra|substr:2:1
                }

                var $cid_quarto {
                  value = ($tamanho_palavra > 3 ? ($palavra|substr:3:1) : "")
                }

                var $cid_tem_formato {
                  value = (("ABCDEFGHIJKLMNOPQRSTUVWXYZ"|contains:$cid_letra) && ("0123456789"|contains:$cid_digito_1) && ("0123456789"|contains:$cid_digito_2) && (($tamanho_palavra == 3) || ($cid_quarto == ".") || ($cid_quarto == ",")))
                }

                conditional {
                  if ($cid_tem_formato) {
                    var.update $observacao_tem_cid {
                      value = true
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    precondition ($observacao_tem_cid == false) {
      error_type = "inputerror"
      error = "Nao informe diagnostico nem codigo CID na observacao. O diagnostico fica somente no atestado."
    }

    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        status    : "Rejeitada"
        observacao: $input.observacao
        updated_at: "now"
      }
    } as $ausencia_rejeitada

    // Auditoria: decisao de rejeicao de ausencia.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "rejeitar_ausencia"
        recurso       : "ausencia"
        registro_id   : $ausencia_atual.id
        justificativa : $input.observacao
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Ausencia rejeitada com sucesso."
    ausencia: $ausencia_rejeitada
  }

  guid = "MHw4Su1K1n606zAdO_w2e4FUZuM"
}