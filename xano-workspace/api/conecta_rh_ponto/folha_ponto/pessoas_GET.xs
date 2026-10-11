// Pessoas cuja folha de ponto quem pede pode consultar (tarefa 81): RH e Admin, todos; os
// demais, a si mesmos, quem os tem como superior direto e, de quem nao tem superior, o
// departamento que gerenciam. Devolve so dados de trabalho e a data do primeiro ponto.
query "folha_ponto/pessoas" verb=GET {
  api_group = "ConectaRH - Ponto"
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }


    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $ve_todos {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    precondition ($ve_todos || $colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    // Quem a pessoa pode ver (tarefa 81): RH e Admin, todos; os demais, a si mesmos, quem os
    // tem como superior direto e, de quem nao tem superior, o departamento que gerenciam.
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
      output = ["id", "nome", "departamento_id", "cargo_id", "status", "superior_colaborador_id", "data_admissao", "user_id"]
    } as $todos_colaboradores

    var $visiveis {
      value = []
    }

    var $ids_visiveis {
      value = []
    }

    foreach ($todos_colaboradores) {
      each as $c {
        var $e_eu {
          value = ($colaborador_autenticado != null && $c.id == $colaborador_autenticado.id)
        }

        var $posso_ver {
          value = ($ve_todos || $e_eu || ($colaborador_autenticado != null && ($c.superior_colaborador_id == $colaborador_autenticado.id || ($c.superior_colaborador_id == null && $departamento_gerido_id != null && $c.departamento_id == $departamento_gerido_id))))
        }

        conditional {
          if ($posso_ver) {
            var.update $visiveis {
              value = $visiveis|push:$c
            }

            var.update $ids_visiveis {
              value = $ids_visiveis|push:$c.id
            }
          }
        }
      }
    }

    var $pessoas {
      value = []
    }

    foreach ($visiveis) {
      each as $p {
        db.query registro_ponto {
          where = $db.registro_ponto.colaborador_id == $p.id
          sort = {registro_ponto.data: "asc"}
          return = {type: "single"}
          output = ["data"]
        } as $primeiro

        var.update $pessoas {
          value = $pessoas|push:{id: $p.id, nome: $p.nome, departamento_id: $p.departamento_id, cargo_id: $p.cargo_id, status: $p.status, superior_colaborador_id: $p.superior_colaborador_id, data_admissao: $p.data_admissao, primeiro_registro: ($primeiro != null ? $primeiro.data : null), e_voce: ($colaborador_autenticado != null && $p.id == $colaborador_autenticado.id)}
        }
      }
    }
  }

  response = {
    sucesso   : true
    ve_todos  : $ve_todos
    pessoas   : $pessoas
  }

  guid = "conectahr-folha-ponto-pessoas-get-0001"
}
