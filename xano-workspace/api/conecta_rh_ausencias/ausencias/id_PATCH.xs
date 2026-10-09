// Atualiza uma solicitacao de ausencia do usuario autenticado.
// Somente o proprietario pode alterar enquanto estiver Pendente.
// Preserva o comprovante e a observacao quando nao forem enviados.
query "ausencias/{id}" verb=PATCH {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
    text tipo filters=trim
    date data_inicio
    date data_fim
    text motivo_tipo filters=trim
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
  
    // Localiza o colaborador vinculado ao usuario.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Confere o status profissional.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem atualizar ausencias."
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
  
    // Confere se a ausencia pertence ao usuario autenticado.
    precondition ($ausencia_atual.colaborador_id == $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para alterar esta ausencia."
    }
  
    // Somente registros Pendentes podem ser alterados.
    var $status_ausencia {
      value = $ausencia_atual.status|trim|to_upper
    }
  
    precondition ($status_ausencia == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente ausencias com status Pendente podem ser alteradas."
    }
  
    // Valida o periodo informado.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }
  
    // Motivo escolhido de uma lista fechada (sem texto livre: evita diagnostico).
    precondition ($input.motivo_tipo == "consulta" || $input.motivo_tipo == "doenca" || $input.motivo_tipo == "acompanhamento_familiar" || $input.motivo_tipo == "outro") {
      error_type = "inputerror"
      error = "Motivo invalido. Escolha: consulta, doenca, acompanhamento_familiar ou outro."
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

    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "Falta" || $input.tipo == "Atestado" || $input.tipo == "Afastamento" || $input.tipo == "Licenca" || $input.tipo == "Outro") {
      error_type = "inputerror"
      error = "Tipo de ausencia invalido."
    }
  
    // Mantem o comprovante atual (o upload nao e suportado no plano atual do Xano).
    var $comprovante_final {
      value = $ausencia_atual.comprovante
    }
  
    // Mantem a observacao atual quando nenhuma nova for enviada.
    var $observacao_final {
      value = $ausencia_atual.observacao
    }
  
    // Atualiza a observacao apenas quando ela for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }
  
    // Atualiza somente os campos permitidos.
    db.edit ausencia {
      field_name = "id"
      field_value = $ausencia_atual.id
      data = {
        tipo       : $input.tipo
        data_inicio: $input.data_inicio
        data_fim   : $input.data_fim
        motivo_tipo: $input.motivo_tipo
        comprovante: $comprovante_final
        observacao : $observacao_final
        updated_at : "now"
      }
    } as $ausencia_atualizada
  }

  response = {
    sucesso : true
    mensagem: "Ausencia atualizada com sucesso."
    ausencia: $ausencia_atualizada
  }

  guid = "9kQ5xEyPrB2AFO7mOKPW0NS0N-s"
}