// Formularios de metas de um ciclo (change ciclo-de-metas, D5): RH e Admin veem todas as pessoas
// ativas; quem e superior direto ou gestor de departamento ve a propria equipe; os demais recebem a
// lista vazia. Cada pessoa vem com o departamento e a data de envio de cada etapa (nula se nao
// enviou). So leitura.
query "formularios_meta" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int ciclo_id
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $meu_colaborador_id {
      value = ($colaborador_autenticado != null ? $colaborador_autenticado.id : 0)
    }

    var $e_rh {
      value = (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN"))
    }

    db.get ciclo_metas {
      field_name = "id"
      field_value = $input.ciclo_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de metas nao encontrado."
    }

    var $etapa_aberta {
      value = null
    }

    conditional {
      if (($ciclo.etapa1_inicio <= $hoje) && ($hoje <= $ciclo.etapa1_fim)) {
        var.update $etapa_aberta {
          value = 1
        }
      }
    }

    conditional {
      if (($ciclo.etapa2_inicio <= $hoje) && ($hoje <= $ciclo.etapa2_fim)) {
        var.update $etapa_aberta {
          value = 2
        }
      }
    }

    conditional {
      if (($ciclo.etapa3_inicio <= $hoje) && ($hoje <= $ciclo.etapa3_fim)) {
        var.update $etapa_aberta {
          value = 3
        }
      }
    }

    // Departamentos que a pessoa gere, como texto ",1,5," (contains em lista nao funciona).
    db.query departamento {
      where = $db.departamento.gestor_colaborador_id == $meu_colaborador_id
      return = {type: "list"}
      output = ["id"]
    } as $departamentos_geridos

    var $departamentos_texto {
      value = ","
    }

    foreach ($departamentos_geridos) {
      each as $dg {
        var.update $departamentos_texto {
          value = $departamentos_texto ~ ($dg.id|to_text) ~ ","
        }
      }
    }

    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "departamento_id", "superior_colaborador_id"]
    } as $pessoas_ativas

    var $pessoas {
      value = []
    }

    foreach ($pessoas_ativas) {
      each as $p {
        var $da_equipe {
          value = (($p.id != $meu_colaborador_id) && (($p.superior_colaborador_id == $meu_colaborador_id) || (($p.departamento_id != null) && ($departamentos_texto|contains:("," ~ ($p.departamento_id|to_text) ~ ",")))))
        }

        conditional {
          if ($e_rh || $da_equipe) {
            db.query formulario_meta {
              where = $db.formulario_meta.ciclo_metas_id == $ciclo.id && $db.formulario_meta.colaborador_id == $p.id
              return = {type: "single"}
            } as $form_pessoa

            var $departamento_nome {
              value = null
            }

            conditional {
              if ($p.departamento_id != null) {
                db.get departamento {
                  field_name = "id"
                  field_value = $p.departamento_id
                  output = ["id", "nome"]
                } as $departamento_pessoa

                var.update $departamento_nome {
                  value = ($departamento_pessoa != null ? $departamento_pessoa.nome : null)
                }
              }
            }

            var.update $pessoas {
              value = $pessoas|push:{colaborador_id: $p.id, nome: $p.nome, departamento_id: $p.departamento_id, departamento: $departamento_nome, formulario_id: ($form_pessoa != null ? $form_pessoa.id : null), etapa1_enviada_em: ($form_pessoa != null ? $form_pessoa.etapa1_enviada_em : null), etapa2_enviada_em: ($form_pessoa != null ? $form_pessoa.etapa2_enviada_em : null), etapa3_enviada_em: ($form_pessoa != null ? $form_pessoa.etapa3_enviada_em : null)}
            }
          }
        }
      }
    }
  }

  response = {
    sucesso     : true
    hoje        : $hoje
    ciclo       : $ciclo
    etapa_aberta: $etapa_aberta
    pessoas     : $pessoas
  }

  guid = "conectahr-formularios-meta-get-0001"
}
