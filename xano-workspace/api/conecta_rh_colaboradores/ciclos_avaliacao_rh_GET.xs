// Ciclos de avaliacao de desempenho para o RH (change pesquisa-clima-e-avaliacao-360, D5), numa chamada:
// os ciclos ativos, dos mais novos para os mais antigos, com quantas avaliacoes foram atribuidas, enviadas,
// estao em aberto e foram canceladas, e as autoavaliacoes e as do gestor (sem as canceladas; Figma 249:5068); as contestacoes abertas com os nomes (avaliado, avaliador, ciclo) e a
// nota; os departamentos ativos (para a atribuicao em lote) e as pessoas (para a avulsa). So RH e Admin.
query "ciclos_avaliacao_rh" verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.query ciclo_avaliacao {
      where = $db.ciclo_avaliacao.ativo == true
      sort = {ciclo_avaliacao.created_at: "desc"}
      return = {type: "list"}
    } as $ciclos_ativos

    var $ciclos {
      value = []
    }

    foreach ($ciclos_ativos) {
      each as $ciclo {
        db.query avaliacao {
          where = $db.avaliacao.ciclo_avaliacao_id == $ciclo.id
          return = {type: "list"}
          output = ["id", "status", "relacao_avaliador"]
        } as $avaliacoes_ciclo

        var $contagens {
          value = {total: 0, enviadas: 0, abertas: 0, canceladas: 0, auto_total: 0, auto_enviadas: 0, gestor_total: 0, gestor_enviadas: 0}
        }

        foreach ($avaliacoes_ciclo) {
          each as $av {
            var $chave {
              value = ($av.status == "enviada" ? "enviadas" : ($av.status == "cancelada" ? "canceladas" : "abertas"))
            }

            var.update $contagens {
              value = $contagens|set:$chave:(($contagens|get:$chave) + 1)|set:"total":(($contagens|get:"total") + 1)
            }

            // Autoavaliacoes e avaliacoes do gestor, sem as canceladas: "atribuidas" e "enviadas".
            conditional {
              if ((($av.relacao_avaliador == "autoavaliacao") || ($av.relacao_avaliador == "gestor")) && ($av.status != "cancelada")) {
                var $prefixo {
                  value = ($av.relacao_avaliador == "autoavaliacao" ? "auto" : "gestor")
                }

                var $chave_total {
                  value = $prefixo ~ "_total"
                }

                var $chave_enviadas {
                  value = $prefixo ~ "_enviadas"
                }

                var.update $contagens {
                  value = $contagens|set:$chave_total:(($contagens|get:$chave_total) + 1)
                }

                conditional {
                  if ($av.status == "enviada") {
                    var.update $contagens {
                      value = $contagens|set:$chave_enviadas:(($contagens|get:$chave_enviadas) + 1)
                    }
                  }
                }
              }
            }
          }
        }

        var.update $ciclos {
          value = $ciclos|push:($ciclo|set:"contagens":$contagens)
        }
      }
    }

    db.query contestacao_avaliacao {
      where = $db.contestacao_avaliacao.status == "aberta"
      sort = {contestacao_avaliacao.created_at: "asc"}
      return = {type: "list"}
    } as $contestacoes_abertas

    var $contestacoes {
      value = []
    }

    foreach ($contestacoes_abertas) {
      each as $contestacao {
        db.get avaliacao {
          field_name = "id"
          field_value = $contestacao.avaliacao_id
        } as $avaliacao_contestada

        db.get colaborador {
          field_name = "id"
          field_value = $contestacao.colaborador_id
          output = ["id", "nome"]
        } as $avaliado

        var $avaliador_nome {
          value = null
        }

        var $ciclo_nome {
          value = null
        }

        conditional {
          if ($avaliacao_contestada != null) {
            db.get user {
              field_name = "id"
              field_value = $avaliacao_contestada.user_id
              output = ["id", "nome"]
            } as $avaliador

            var.update $avaliador_nome {
              value = ($avaliador != null ? $avaliador.nome : null)
            }

            conditional {
              if ($avaliacao_contestada.ciclo_avaliacao_id != null) {
                db.get ciclo_avaliacao {
                  field_name = "id"
                  field_value = $avaliacao_contestada.ciclo_avaliacao_id
                  output = ["id", "nome"]
                } as $ciclo_contestado

                var.update $ciclo_nome {
                  value = ($ciclo_contestado != null ? $ciclo_contestado.nome : null)
                }
              }
            }
          }
        }

        var.update $contestacoes {
          value = $contestacoes|push:{
            id               : $contestacao.id
            avaliacao_id     : $contestacao.avaliacao_id
            ciclo_avaliacao_id: ($avaliacao_contestada != null ? $avaliacao_contestada.ciclo_avaliacao_id : null)
            motivo           : $contestacao.motivo
            criada_em        : $contestacao.created_at
            avaliado_nome    : ($avaliado != null ? $avaliado.nome : null)
            avaliador_nome   : $avaliador_nome
            relacao_avaliador: ($avaliacao_contestada != null ? $avaliacao_contestada.relacao_avaliador : null)
            nota             : ($avaliacao_contestada != null ? $avaliacao_contestada.nota : null)
            ciclo_nome       : $ciclo_nome
          }
        }
      }
    }

    db.query departamento {
      where = $db.departamento.ativo == true
      sort = {departamento.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome"]
    } as $departamentos

    // Pessoas que podem ser avaliadas ou avaliar (atribuicao avulsa: par, subordinado, rh).
    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "user_id", "departamento_id"]
    } as $pessoas
  }

  response = {
    sucesso      : true
    hoje         : $hoje
    ciclos       : $ciclos
    contestacoes : $contestacoes
    departamentos: $departamentos
    pessoas      : $pessoas
  }

  guid = "conectahr-ciclos-avaliacao-rh-get-0001"
}
