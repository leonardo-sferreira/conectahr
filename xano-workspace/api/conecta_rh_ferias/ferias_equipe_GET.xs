// Ferias da equipe no periodo (calendario do gestor): quem esta de ferias aprovadas, concluidas
// ou com pedido em analise entre `desde` e `ate`, para o gestor nao deixar muita gente sair junto.
// Escopo da folha de ponto (tarefa 81): RH e Admin, todos; os demais, a si mesmos, quem os tem
// como superior direto e, de quem nao tem superior, o departamento que gerenciam.
// Devolve so nome, departamento, periodo, dias e situacao (sem observacao nem abono).
query ferias_equipe verb=GET {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    date desde
    date ate
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $ve_todos {
      value = (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN"))
    }

    precondition ($ve_todos || ($colaborador_autenticado != null)) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    precondition ($input.ate >= $input.desde) {
      error_type = "inputerror"
      error = "O fim do periodo deve ser igual ou depois do inicio."
    }

    var $departamento_gerido_id {
      value = null
    }

    conditional {
      if ($colaborador_autenticado != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerido

        conditional {
          if ($departamento_gerido != null) {
            var.update $departamento_gerido_id {
              value = $departamento_gerido.id
            }
          }
        }
      }
    }

    db.query colaborador {
      where = $db.colaborador.anonimizado_em == null
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "departamento_id", "status", "superior_colaborador_id"]
    } as $todos_colaboradores

    var $pessoas_visiveis {
      value = 0
    }

    var $ferias_equipe {
      value = []
    }

    foreach ($todos_colaboradores) {
      each as $c {
        var $e_eu {
          value = (($colaborador_autenticado != null) && ($c.id == $colaborador_autenticado.id))
        }

        var $subordinado {
          value = (($colaborador_autenticado != null) && (($c.superior_colaborador_id == $colaborador_autenticado.id) || (($c.superior_colaborador_id == null) && ($departamento_gerido_id != null) && ($c.departamento_id == $departamento_gerido_id))))
        }

        conditional {
          if (($ve_todos || $e_eu || $subordinado) && ($c.status != "Desligado")) {
            var.update $pessoas_visiveis {
              value = $pessoas_visiveis + 1
            }

            db.query ferias {
              where = $db.ferias.colaborador_id == $c.id && $db.ferias.data_inicio <= $input.ate && $db.ferias.data_fim >= $input.desde
              sort = {ferias.data_inicio: "asc"}
              return = {type: "list"}
              output = ["id", "data_inicio", "data_fim", "quantidade_dias", "status"]
            } as $ferias_da_pessoa

            foreach ($ferias_da_pessoa) {
              each as $f {
                conditional {
                  if (($f.status == "Aprovada") || ($f.status == "Concluida") || ($f.status == "Pendente")) {
                    var.update $ferias_equipe {
                      value = $ferias_equipe|push:{id: $f.id, colaborador_id: $c.id, nome: $c.nome, departamento_id: $c.departamento_id, data_inicio: $f.data_inicio, data_fim: $f.data_fim, quantidade_dias: $f.quantidade_dias, status: $f.status, e_voce: $e_eu}
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
    sucesso : true
    ve_todos: $ve_todos
    pessoas : $pessoas_visiveis
    ferias  : $ferias_equipe
  }

  guid = "conectahr-ferias-equipe-get-0001"
}
