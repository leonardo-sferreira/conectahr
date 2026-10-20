// Atribui avaliacoes em lote num ciclo em andamento (change pesquisa-clima-e-avaliacao-360, D6), em vez de
// uma chamada por avaliacao: para cada ficha que nao esta desligada e tem conta (de um departamento ou de
// todos), a autoavaliacao e/ou a avaliacao do gestor (o superior direto; sem ele, o gestor do departamento;
// ninguem avalia a si mesmo como gestor). O que ja existe no ciclo (mesma pessoa, mesmo avaliador, mesma
// relacao, nao cancelada) e pulado. Cada avaliador recebe um aviso no sino e um e-mail (Figma 249:5364), um por lote. Auditado. So RH e Admin.
query "ciclos_avaliacao/{id}/atribuir" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int? departamento_id?
    bool autoavaliacao
    bool gestor
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    precondition ($input.autoavaliacao || $input.gestor) {
      error_type = "inputerror"
      error = "Escolha pelo menos um tipo de avaliacao."
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    precondition ($ciclo.status == "em_andamento") {
      error_type = "inputerror"
      error = "O ciclo de avaliacao precisa estar em andamento."
    }

    // "!= null" trata 0 como nulo nesta plataforma: o departamento vem como texto ("" = todos).
    var $departamento_texto {
      value = ($input.departamento_id|to_text)
    }

    var $todos_departamentos {
      value = (($departamento_texto == "") || ($departamento_texto == "0"))
    }

    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      return = {type: "list"}
      output = ["id", "nome", "user_id", "departamento_id", "superior_colaborador_id"]
    } as $fichas

    db.query avaliacao {
      where = $db.avaliacao.ciclo_avaliacao_id == $ciclo.id && $db.avaliacao.status != "cancelada"
      return = {type: "list"}
      output = ["colaborador_id", "user_id", "relacao_avaliador"]
    } as $existentes

    // Chaves "colaborador:avaliador:relacao" ja atribuidas, como texto.
    var $existentes_texto {
      value = ","
    }

    foreach ($existentes) {
      each as $ex {
        var.update $existentes_texto {
          value = $existentes_texto ~ ($ex.colaborador_id|to_text) ~ ":" ~ ($ex.user_id|to_text) ~ ":" ~ $ex.relacao_avaliador ~ ","
        }
      }
    }

    var $criadas {
      value = 0
    }

    var $puladas {
      value = 0
    }

    var $sem_gestor {
      value = 0
    }

    // Avaliadores a avisar (uma vez cada), como texto ",user_id,".
    var $avisar_texto {
      value = ","
    }

    var $avisar {
      value = []
    }

    foreach ($fichas) {
      each as $ficha {
        conditional {
          if (($ficha.user_id != null) && ($todos_departamentos || (($ficha.departamento_id|to_text) == $departamento_texto))) {
            // Quem avalia em cada relacao pedida: [{user_id, relacao}].
            var $pares {
              value = []
            }

            conditional {
              if ($input.autoavaliacao) {
                var.update $pares {
                  value = $pares|push:{user_id: $ficha.user_id, relacao: "autoavaliacao"}
                }
              }
            }

            conditional {
              if ($input.gestor) {
                var $gestor_colaborador_id {
                  value = $ficha.superior_colaborador_id
                }

                conditional {
                  if ($gestor_colaborador_id == null) {
                    db.get departamento {
                      field_name = "id"
                      field_value = $ficha.departamento_id
                      output = ["id", "gestor_colaborador_id"]
                    } as $dep_ficha

                    var.update $gestor_colaborador_id {
                      value = ($dep_ficha != null ? $dep_ficha.gestor_colaborador_id : null)
                    }
                  }
                }

                var $gestor_user_id {
                  value = null
                }

                conditional {
                  if (($gestor_colaborador_id != null) && ($gestor_colaborador_id != $ficha.id)) {
                    db.get colaborador {
                      field_name = "id"
                      field_value = $gestor_colaborador_id
                      output = ["id", "user_id", "status"]
                    } as $gestor_ficha

                    conditional {
                      if (($gestor_ficha != null) && ($gestor_ficha.status != "Desligado")) {
                        var.update $gestor_user_id {
                          value = $gestor_ficha.user_id
                        }
                      }
                    }
                  }
                }

                conditional {
                  if (($gestor_user_id != null) && ($gestor_user_id != $ficha.user_id)) {
                    var.update $pares {
                      value = $pares|push:{user_id: $gestor_user_id, relacao: "gestor"}
                    }
                  }

                  else {
                    var.update $sem_gestor {
                      value = $sem_gestor + 1
                    }
                  }
                }
              }
            }

            foreach ($pares) {
              each as $par {
                var $chave {
                  value = "," ~ ($ficha.id|to_text) ~ ":" ~ ($par.user_id|to_text) ~ ":" ~ $par.relacao ~ ","
                }

                conditional {
                  if ($existentes_texto|contains:$chave) {
                    var.update $puladas {
                      value = $puladas + 1
                    }
                  }

                  else {
                    db.add avaliacao {
                      data = {
                        colaborador_id    : $ficha.id
                        user_id           : $par.user_id
                        ciclo_avaliacao_id: $ciclo.id
                        relacao_avaliador : $par.relacao
                        periodo_incio     : $ciclo.data_inicio
                        periodo_fim       : $ciclo.data_fim
                        status            : "pendente"
                        updated_at        : "now"
                      }
                    } as $avaliacao_criada

                    var.update $existentes_texto {
                      value = $existentes_texto ~ ($ficha.id|to_text) ~ ":" ~ ($par.user_id|to_text) ~ ":" ~ $par.relacao ~ ","
                    }

                    var.update $criadas {
                      value = $criadas + 1
                    }

                    // Agulha numa variavel: o Xano tira os parenteses do argumento do filtro.
                    var $agulha_aviso {
                      value = "," ~ ($par.user_id|to_text) ~ ","
                    }

                    conditional {
                      if (($avisar_texto|contains:$agulha_aviso) == false) {
                        var.update $avisar_texto {
                          value = $avisar_texto ~ ($par.user_id|to_text) ~ ","
                        }

                        var.update $avisar {
                          value = $avisar|push:$par.user_id
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    foreach ($avisar) {
      each as $avaliador_user_id {
        function.run "ConectaHR/notificar" {
          input = {destinatario_user_id: $avaliador_user_id, autor_user_id: $usuario_autenticado.id, tipo: "avaliacao_disponivel", titulo: "Avaliações para fazer", mensagem: "Você tem avaliações do ciclo " ~ $ciclo.nome ~ " para preencher. Elas estão na sua Trajetória.", recurso: "avaliacao", registro_id: $ciclo.id}
        } as $aviso_retorno

        // E-mail, como em avaliacoes POST: sem preferencia registrada, o canal fica ligado.
        db.query preferencia_aviso {
          where = $db.preferencia_aviso.user_id == $avaliador_user_id && $db.preferencia_aviso.assunto == "avaliacoes_metas"
          return = {type: "single"}
        } as $preferencia_email

        conditional {
          if (($preferencia_email == null) || ($preferencia_email.email == true)) {
            db.get user {
              field_name = "id"
              field_value = $avaliador_user_id
              output = ["id", "nome", "email"]
            } as $avaliador_conta

            conditional {
              if (($avaliador_conta != null) && ($avaliador_conta.email != null) && ($avaliador_conta.email != "")) {
                db.add email_outbox {
                  data = {
                    destinatario_email: $avaliador_conta.email
                    destinatario_nome : $avaliador_conta.nome
                    assunto           : "ConectaRH - Avaliacoes para fazer"
                    corpo             : "Ola " ~ $avaliador_conta.nome ~ ",\n\nVoce tem avaliacoes do ciclo " ~ $ciclo.nome ~ " para preencher no ConectaRH. Elas estao na sua Trajetoria.\n\nEste e um aviso automatico."
                    chave_idempotencia: "avaliacoes_lote_" ~ ($ciclo.id|to_text) ~ "_" ~ ($avaliador_user_id|to_text) ~ "_" ~ (now|format_timestamp:"YmdHis":"UTC")
                  }
                } as $email_avaliador
              }
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "atribuir_avaliacoes_lote"
        recurso      : "ciclo_avaliacao"
        registro_id  : $ciclo.id
        resultado    : "sucesso"
        justificativa: ($criadas|to_text) ~ " criadas, " ~ ($puladas|to_text) ~ " ja existiam"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    mensagem  : "Avaliacoes atribuidas."
    criadas   : $criadas
    puladas   : $puladas
    sem_gestor: $sem_gestor
  }

  guid = "conectahr-ciclos-avaliacao-atribuir-post-0001"
}
