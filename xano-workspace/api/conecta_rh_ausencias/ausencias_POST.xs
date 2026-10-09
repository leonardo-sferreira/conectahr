// Cria uma solicitacao de ausencia para o usuario autenticado.
// Permite comprovante e observacao opcionais.
// Nao recebe colaborador_id ou user_id.
query ausencias verb=POST {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    text tipo filters=trim
    date data_inicio
    date data_fim
    text motivo_tipo filters=trim
    attachment? comprovante?
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
  
    // Contas inativas nao podem criar ausencias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Localiza o colaborador pelo token.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Somente colaborador profissionalmente ativo
    // pode criar uma solicitacao.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem registrar ausencias."
    }
  
    // Valida o periodo.
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

    // Valida o tipo conforme o Enum da tabela.
    precondition ($input.tipo == "Falta" || $input.tipo == "Atestado" || $input.tipo == "Afastamento" || $input.tipo == "Licenca" || $input.tipo == "Outro") {
      error_type = "inputerror"
      error = "Tipo invalido. Use Falta, Atestado, Afastamento, Licenca ou Outro."
    }
  
    // Prepara o comprovante opcional.
    var $comprovante_metadata {
      value = null
    }
  
    // Armazena o arquivo como privado quando enviado.
    conditional {
      if ($input.comprovante != null) {
        storage.create_attachment {
          value = $input.comprovante
          access = "private"
          filename = ""
        } as $arquivo_privado
      
        var.update $comprovante_metadata {
          value = $arquivo_privado
        }
      }
    }
  
    // Cria a solicitacao.
    db.add ausencia {
      data = {
        colaborador_id: $colaborador_autenticado.id
        tipo          : $input.tipo
        data_inicio   : $input.data_inicio
        data_fim      : $input.data_fim
        motivo_tipo   : $input.motivo_tipo
        comprovante   : $comprovante_metadata
        status        : "Pendente"
        observacao    : $input.observacao
        updated_at    : "now"
      }
    } as $ausencia_criada
  }

  response = {
    sucesso : true
    mensagem: "Solicitacao de ausencia criada com sucesso e enviada para analise."
    ausencia: $ausencia_criada
  }

  guid = "IGyrP5wYk0dFAOKGhL_AkayBL1s"
}