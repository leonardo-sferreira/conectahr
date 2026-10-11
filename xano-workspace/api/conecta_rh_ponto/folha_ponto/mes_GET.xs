// Folha de ponto de um mes (tarefa 81): registros, ausencias (so tipo, periodo e status) e
// ferias aprovadas das pessoas que quem pede pode ver (mesmo escopo de folha_ponto/pessoas).
// Com colaborador_id, so dessa pessoa, e com as correcoes dos registros. Sem ele, de todas
// (resumo da equipe ou da empresa, para o fechamento do mes).
query "folha_ponto/mes" verb=GET {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int ano filters=min:2000|max:2100
    int mes filters=min:1|max:12
    int? colaborador_id?
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

    precondition ($input.colaborador_id == null || ($ids_visiveis|contains:$input.colaborador_id)) {
      error_type = "accessdenied"
      error = "Voce nao pode consultar a folha de ponto desta pessoa."
    }

    var $alvos {
      value = $ids_visiveis
    }

    conditional {
      if ($input.colaborador_id != null) {
        var.update $alvos {
          value = []|push:$input.colaborador_id
        }
      }
    }

    var $inicio {
      value = ($input.ano|to_text) ~ "-" ~ ($input.mes < 10 ? "0" ~ ($input.mes|to_text) : ($input.mes|to_text)) ~ "-01"
    }

    var $fim {
      value = ($input.mes == 12 ? (($input.ano + 1)|to_text) ~ "-01-01" : ($input.ano|to_text) ~ "-" ~ ($input.mes < 9 ? "0" ~ (($input.mes + 1)|to_text) : (($input.mes + 1)|to_text)) ~ "-01")
    }

    db.query registro_ponto {
      where = $db.registro_ponto.data >= $inicio && $db.registro_ponto.data < $fim
      sort = {registro_ponto.data: "asc"}
      return = {type: "list"}
    } as $registros_mes

    var $registros {
      value = []
    }

    foreach ($registros_mes) {
      each as $r {
        conditional {
          if ($alvos|contains:$r.colaborador_id) {
            var.update $registros {
              value = $registros|push:$r
            }
          }
        }
      }
    }

    db.query ausencia {
      where = $db.ausencia.data_inicio < $fim && $db.ausencia.data_fim >= $inicio
      return = {type: "list"}
      output = ["id", "colaborador_id", "tipo", "data_inicio", "data_fim", "status"]
    } as $ausencias_mes

    var $ausencias {
      value = []
    }

    foreach ($ausencias_mes) {
      each as $a {
        conditional {
          if ($alvos|contains:$a.colaborador_id) {
            var.update $ausencias {
              value = $ausencias|push:$a
            }
          }
        }
      }
    }

    db.query ferias {
      where = $db.ferias.data_inicio < $fim && $db.ferias.data_fim >= $inicio && ($db.ferias.status == "Aprovada" || $db.ferias.status == "Concluida")
      return = {type: "list"}
      output = ["id", "colaborador_id", "data_inicio", "data_fim", "status"]
    } as $ferias_mes

    var $ferias_lista {
      value = []
    }

    foreach ($ferias_mes) {
      each as $f {
        conditional {
          if ($alvos|contains:$f.colaborador_id) {
            var.update $ferias_lista {
              value = $ferias_lista|push:$f
            }
          }
        }
      }
    }

    var $correcoes {
      value = []
    }

    conditional {
      if ($input.colaborador_id != null) {
        db.query correcao_ponto {
          where = $db.correcao_ponto.colaborador_id == $input.colaborador_id
          sort = {correcao_ponto.created_at: "desc"}
          return = {type: "list"}
        } as $correcoes_da_pessoa

        var.update $correcoes {
          value = $correcoes_da_pessoa
        }
      }
    }
  }

  response = {
    sucesso   : true
    inicio    : $inicio
    fim       : $fim
    registros : $registros
    ausencias : $ausencias
    ferias    : $ferias_lista
    correcoes : $correcoes
  }

  guid = "conectahr-folha-ponto-mes-get-0001"
}
