// Pesquisa global de colaboradores por nome, CPF, matricula (id), cargo
// ou departamento. Gestor recebe somente resultados do departamento que
// gerencia (cada gestor gerencia um unico departamento); RH, ADMIN e
// COLABORADOR recebem qualquer colaborador ativo. O CPF pode ser usado
// como termo de busca, mas nunca e retornado no resultado.
query "colaboradores/buscar" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text termo filters=trim|min:2|max:100
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    // Escopo do Gestor: departamento que ele gerencia (se houver).
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

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

    // Resolve, se houver, um cargo e um departamento cujo nome bate com o termo.
    db.query cargo {
      return = {type: "list"}
      output = ["id", "nome"]
    } as $todos_cargos

    db.query departamento {
      return = {type: "list"}
      output = ["id", "nome"]
    } as $todos_departamentos

    var $cargo_id_encontrado {
      value = null
    }

    foreach ($todos_cargos) {
      each as $cargo_item {
        conditional {
          if ($cargo_item.nome|icontains:$input.termo) {
            var.update $cargo_id_encontrado {
              value = $cargo_item.id
            }
          }
        }
      }
    }

    var $departamento_id_encontrado {
      value = null
    }

    foreach ($todos_departamentos) {
      each as $departamento_item {
        conditional {
          if ($departamento_item.nome|icontains:$input.termo) {
            var.update $departamento_id_encontrado {
              value = $departamento_item.id
            }
          }
        }
      }
    }

    // Candidatos: ativos, e dentro do escopo do gestor quando aplicavel.
    db.query colaborador {
      where = ($db.colaborador.status == "Ativo" && ($departamento_escopo_id == null || $db.colaborador.departamento_id == $departamento_escopo_id))
      return = {type: "list"}
      output = ["id", "nome", "cpf", "cargo_id", "departamento_id"]
    } as $candidatos

    var $resultados {
      value = []
    }

    foreach ($candidatos) {
      each as $candidato_item {
        var $id_texto {
          value = ($candidato_item.id)|to_text
        }

        var $confere {
          value = ($candidato_item.nome|icontains:$input.termo) || ($candidato_item.cpf == $input.termo) || ($id_texto == $input.termo) || ($cargo_id_encontrado != null && $candidato_item.cargo_id == $cargo_id_encontrado) || ($departamento_id_encontrado != null && $candidato_item.departamento_id == $departamento_id_encontrado)
        }

        conditional {
          if ($confere) {
            var.update $resultados {
              value = $resultados|push:{
                id            : $candidato_item.id
                nome          : $candidato_item.nome
                cargo_id      : $candidato_item.cargo_id
                departamento_id: $candidato_item.departamento_id
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso      : true
    resultados   : $resultados
    cargos       : $todos_cargos
    departamentos: $todos_departamentos
  }

  guid = "conectahr-colaboradores-buscar-get-0001"
}
