// Central de tarefas e pendencias por perfil (item 1.7). Reune, numa
// unica consulta: pendencias pessoais (senha temporaria, cadastro
// incompleto, ponto do dia, minhas ferias pendentes), fila de decisao
// para RH/ADMIN/GESTOR (ferias, documentos e desligamentos pendentes,
// restritos ao departamento quando o perfil e GESTOR) e o dashboard do
// gestor (tamanho da equipe, ferias proximas, ausencias da equipe e
// situacao do ponto do dia).
// Gap consciente: correcao de ponto (item 4.2), avaliacoes e metas/PDI
// (secao 6) ainda nao existem no codigo, entao nao entram aqui ainda.
query "central_de_tarefas" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    // Colaborador vinculado a conta autenticada, se houver.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    // ---- Pendencias pessoais ----

    var $cadastro_incompleto {
      value = false
    }

    var $meu_ponto_status_hoje {
      value = null
    }

    var $minhas_ferias_pendentes {
      value = []
    }

    conditional {
      if ($colaborador_autenticado != null) {
        var.update $cadastro_incompleto {
          value = ($colaborador_autenticado.data_nascimento == null || $colaborador_autenticado.cep == null || $colaborador_autenticado.banco == null)
        }

        db.query registro_ponto {
          where = $db.registro_ponto.colaborador_id == $colaborador_autenticado.id && $db.registro_ponto.data == $hoje
          return = {type: "single"}
        } as $meu_registro_hoje

        conditional {
          if ($meu_registro_hoje != null) {
            var.update $meu_ponto_status_hoje {
              value = $meu_registro_hoje.status
            }
          }
        }

        db.query ferias {
          where = $db.ferias.colaborador_id == $colaborador_autenticado.id && $db.ferias.status == "Pendente"
          return = {type: "list"}
        } as $minhas_ferias_pendentes
      }
    }

    // ---- Escopo de aprovacao: RH/ADMIN veem tudo, GESTOR so a equipe ----

    var $e_aprovador {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR")
    }

    var $departamento_escopo_id {
      value = null
    }

    conditional {
      if ($perfil_autenticado == "GESTOR" && $colaborador_autenticado != null) {
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

    // ---- Fila de aprovacao (ferias, documentos, desligamentos) ----

    var $ferias_pendentes_fila {
      value = []
    }

    var $documentos_pendentes_fila {
      value = []
    }

    var $desligamentos_pendentes_fila {
      value = []
    }

    conditional {
      if ($e_aprovador) {
        db.query ferias {
          where = $db.ferias.status == "Pendente"
          return = {type: "list"}
        } as $ferias_pendentes_todas

        db.query documento {
          where = $db.documento.status == "pendente_analise"
          return = {type: "list"}
        } as $documentos_pendentes_todos

        db.query solicitacao_desligamento {
          where = $db.solicitacao_desligamento.status == "pendente" || $db.solicitacao_desligamento.status == "em_analise"
          return = {type: "list"}
        } as $desligamentos_pendentes_todos

        conditional {
          if ($departamento_escopo_id == null) {
            var.update $ferias_pendentes_fila {
              value = $ferias_pendentes_todas
            }

            var.update $documentos_pendentes_fila {
              value = $documentos_pendentes_todos
            }

            var.update $desligamentos_pendentes_fila {
              value = $desligamentos_pendentes_todos
            }
          }
        }

        conditional {
          if ($departamento_escopo_id != null) {
            foreach ($ferias_pendentes_todas) {
              each as $ferias_item {
                db.get colaborador {
                  field_name = "id"
                  field_value = $ferias_item.colaborador_id
                } as $colaborador_da_ferias

                conditional {
                  if ($colaborador_da_ferias != null && $colaborador_da_ferias.departamento_id == $departamento_escopo_id) {
                    var.update $ferias_pendentes_fila {
                      value = $ferias_pendentes_fila|push:$ferias_item
                    }
                  }
                }
              }
            }

            foreach ($documentos_pendentes_todos) {
              each as $documento_item {
                db.get colaborador {
                  field_name = "id"
                  field_value = $documento_item.colaborador_id
                } as $colaborador_do_documento

                conditional {
                  if ($colaborador_do_documento != null && $colaborador_do_documento.departamento_id == $departamento_escopo_id) {
                    var.update $documentos_pendentes_fila {
                      value = $documentos_pendentes_fila|push:$documento_item
                    }
                  }
                }
              }
            }

            foreach ($desligamentos_pendentes_todos) {
              each as $desligamento_item {
                db.get colaborador {
                  field_name = "id"
                  field_value = $desligamento_item.colaborador_id
                } as $colaborador_do_desligamento

                conditional {
                  if ($colaborador_do_desligamento != null && $colaborador_do_desligamento.departamento_id == $departamento_escopo_id) {
                    var.update $desligamentos_pendentes_fila {
                      value = $desligamentos_pendentes_fila|push:$desligamento_item
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    // ---- Dashboard do gestor ----

    var $tamanho_equipe {
      value = null
    }

    var $ferias_proximas_equipe {
      value = []
    }

    var $ausencias_equipe {
      value = []
    }

    var $ponto_completo_hoje {
      value = 0
    }

    var $ponto_aberto_hoje {
      value = 0
    }

    var $ponto_sem_registro_hoje {
      value = 0
    }

    conditional {
      if ($departamento_escopo_id != null) {
        db.query colaborador {
          where = $db.colaborador.departamento_id == $departamento_escopo_id && $db.colaborador.status == "Ativo"
          return = {type: "list"}
        } as $equipe

        var.update $tamanho_equipe {
          value = $equipe|count
        }

        db.query ferias {
          where = $db.ferias.status == "Aprovada" && $db.ferias.data_inicio >= $hoje
          return = {type: "list"}
        } as $ferias_aprovadas_todas

        db.query ausencia {
          where = $db.ausencia.status == "Aprovada"
          return = {type: "list"}
        } as $ausencias_aprovadas_todas

        foreach ($equipe) {
          each as $membro_equipe {
            // Ferias proximas do membro da equipe.
            foreach ($ferias_aprovadas_todas) {
              each as $ferias_item {
                conditional {
                  if ($ferias_item.colaborador_id == $membro_equipe.id) {
                    var.update $ferias_proximas_equipe {
                      value = $ferias_proximas_equipe|push:$ferias_item
                    }
                  }
                }
              }
            }

            // Ausencias aprovadas do membro da equipe.
            foreach ($ausencias_aprovadas_todas) {
              each as $ausencia_item {
                conditional {
                  if ($ausencia_item.colaborador_id == $membro_equipe.id) {
                    var.update $ausencias_equipe {
                      value = $ausencias_equipe|push:$ausencia_item
                    }
                  }
                }
              }
            }

            // Situacao do ponto do dia do membro da equipe.
            db.query registro_ponto {
              where = $db.registro_ponto.colaborador_id == $membro_equipe.id && $db.registro_ponto.data == $hoje
              return = {type: "single"}
            } as $registro_membro_hoje

            conditional {
              if ($registro_membro_hoje == null) {
                var.update $ponto_sem_registro_hoje {
                  value = $ponto_sem_registro_hoje + 1
                }
              }

              else {
                conditional {
                  if ($registro_membro_hoje.status == "Completo") {
                    var.update $ponto_completo_hoje {
                      value = $ponto_completo_hoje + 1
                    }
                  }

                  else {
                    var.update $ponto_aberto_hoje {
                      value = $ponto_aberto_hoje + 1
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

  response = {
    sucesso                        : true
    minha_senha_primeiro_acesso    : $usuario_autenticado.senha_primeiro_acesso
    meu_cadastro_incompleto        : $cadastro_incompleto
    meu_ponto_status_hoje          : $meu_ponto_status_hoje
    minhas_ferias_pendentes        : $minhas_ferias_pendentes
    fila_ferias_pendentes          : $ferias_pendentes_fila
    fila_documentos_pendentes      : $documentos_pendentes_fila
    fila_desligamentos_pendentes   : $desligamentos_pendentes_fila
    equipe_tamanho                 : $tamanho_equipe
    equipe_ferias_proximas         : $ferias_proximas_equipe
    equipe_ausencias               : $ausencias_equipe
    equipe_ponto_completo_hoje     : $ponto_completo_hoje
    equipe_ponto_aberto_hoje       : $ponto_aberto_hoje
    equipe_ponto_sem_registro_hoje : $ponto_sem_registro_hoje
  }

  guid = "conectahr-central-de-tarefas-get-0001"
}
