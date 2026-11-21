// Cria uma delegacao temporaria de aprovacao. O titular delega a um
// substituto por um escopo e periodo definidos. Bloqueia autoaprovacao
// (titular nao pode delegar para si mesmo). RH/ADMIN podem criar em
// nome de qualquer titular; o proprio usuario pode criar delegando a
// propria autoridade. O substituto e avisado no sino (change notificacoes-de-publicacao, D4).
query delegacoes verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int? titular_user_id?
    int substituto_user_id
    text escopo filters=trim
    date data_inicio
    date data_fim
    text motivo filters=trim|min:5|max:1000
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    // Define o titular: o proprio autenticado, ou outro quando RH/ADMIN informar.
    var $titular_id_final {
      value = $usuario_autenticado.id
    }

    conditional {
      if ($input.titular_user_id != null && $input.titular_user_id != $usuario_autenticado.id) {
        precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
          error_type = "accessdenied"
          error = "Somente RH ou ADMIN podem criar delegacao em nome de outro titular."
        }

        var.update $titular_id_final {
          value = $input.titular_user_id
        }
      }
    }

    // Bloqueia autoaprovacao: titular nao pode delegar para si mesmo.
    precondition ($titular_id_final != $input.substituto_user_id) {
      error_type = "inputerror"
      error = "O titular nao pode delegar para si mesmo."
    }

    db.get user {
      field_name = "id"
      field_value = $titular_id_final
    } as $titular

    precondition ($titular != null) {
      error_type = "notfound"
      error = "Titular nao encontrado."
    }

    db.get user {
      field_name = "id"
      field_value = $input.substituto_user_id
    } as $substituto

    precondition ($substituto != null) {
      error_type = "notfound"
      error = "Substituto nao encontrado."
    }

    precondition ($substituto.ativo) {
      error_type = "inputerror"
      error = "O substituto precisa ter uma conta ativa."
    }

    // Valida o escopo usando os valores exatos do Enum.
    precondition ($input.escopo == "ferias" || $input.escopo == "ausencia" || $input.escopo == "documento" || $input.escopo == "desligamento" || $input.escopo == "correcao_ponto" || $input.escopo == "solicitacao_rh" || $input.escopo == "todas") {
      error_type = "inputerror"
      error = "Escopo invalido."
    }

    // Gestor (change backend-gestor-pendencias, D3): so os escopos que ele decide e um substituto do catalogo.
    // RH e Admin continuam com todos os escopos e qualquer conta ativa.
    conditional {
      if (($perfil_autenticado != "RH") && ($perfil_autenticado != "ADMIN")) {
        precondition (($input.escopo == "ferias") || ($input.escopo == "correcao_ponto") || ($input.escopo == "todas")) {
          error_type = "inputerror"
          error = "O Gestor delega so ferias, correcao de ponto ou todas: as outras decisoes sao do RH."
        }

        var $titular_catalogo_id {
          value = $titular_id_final
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

        precondition ($catalogo_ids|contains:("," ~ ($input.substituto_user_id|to_text) ~ ",")) {
          error_type = "inputerror"
          error = "Escolha o substituto entre as pessoas do seu setor ou os outros Gestores."
        }
      }
    }

    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim nao pode ser anterior a data de inicio."
    }

    db.add delegacao_aprovacao {
      data = {
        titular_user_id     : $titular.id
        substituto_user_id    : $substituto.id
        escopo                  : $input.escopo
        data_inicio               : $input.data_inicio
        data_fim                    : $input.data_fim
        motivo                       : $input.motivo
        criado_por_user_id             : $usuario_autenticado.id
        updated_at                       : "now"
      }
    } as $delegacao_criada

    // Auditoria: criacao de delegacao.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_delegacao_aprovacao"
        recurso    : "delegacao_aprovacao"
        registro_id: $delegacao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    // Avisa o substituto (change notificacoes-de-publicacao, D4): ele passa a receber os pedidos do titular no periodo.
    var $escopo_legivel {
      value = ($input.escopo == "todas") ? "todas as aprovações" : ("as aprovações de " ~ ($input.escopo|replace:"_":" "))
    }

    var $mensagem_delegacao {
      value = ($titular.nome ~ " delegou a você " ~ $escopo_legivel ~ " de " ~ ($input.data_inicio|format_timestamp:"d/m":"UTC") ~ " a " ~ ($input.data_fim|format_timestamp:"d/m":"UTC") ~ ".")|substr:0:1000
    }

    function.run "ConectaHR/notificar" {
      input = {destinatario_user_id: $substituto.id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_novo", titulo: "Você recebeu uma delegação de aprovação", mensagem: $mensagem_delegacao, recurso: "delegacao", registro_id: $delegacao_criada.id}
    } as $aviso_substituto
  }

  response = {
    sucesso   : true
    mensagem  : "Delegacao criada com sucesso."
    delegacao : $delegacao_criada
  }

  guid = "conectahr-delegacoes-post-0001"
}
