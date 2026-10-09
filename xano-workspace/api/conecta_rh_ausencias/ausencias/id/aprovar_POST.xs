// Aprova uma solicitacao de ausencia.
// Operacao permitida somente para RH ou ADMIN.
// Nao altera o colaborador nem exclui o registro.
query "ausencias/{id}/aprovar" verb=POST {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
    text? observacao? filters=trim|max:1000
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
  
    // Somente RH ou ADMIN podem aprovar.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem aprovar ausencias."
    }
  
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
  
    // Somente ausencias Pendentes podem ser aprovadas.
    var $status_atual {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_atual == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente ausencias com status Pendente podem ser aprovadas."
    }
  
    // Confirma que o colaborador ainda existe.
    db.get colaborador {
      field_name = "id"
      field_value = $ausencia_atual.colaborador_id
    } as $colaborador
  
    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador vinculado a ausencia nao encontrado."
    }
  
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

    // Preserva a observacao existente por padrao.
    var $observacao_final {
      value = $ausencia_atual.observacao
    }
  
    // Substitui a observacao somente quando uma nova for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }
  
    // Aprova a ausencia.
    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        status    : "Aprovada"
        observacao: $observacao_final
        updated_at: "now"
      }
    } as $ausencia_aprovada

    // Auditoria: decisao de aprovacao de ausencia.
    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "aprovar_ausencia"
        recurso       : "ausencia"
        registro_id   : $ausencia_atual.id
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Ausencia aprovada com sucesso."
    ausencia: $ausencia_aprovada
  }

  guid = "4O4xdTdSyFE1ljfTuGbsFaasY2g"
}