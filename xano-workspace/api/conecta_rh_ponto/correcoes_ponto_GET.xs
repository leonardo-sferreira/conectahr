// Lista solicitacoes de correcao de ponto pendentes de decisao.
// RH/ADMIN veem todas; Gestor ve somente as do departamento que gerencia.
query correcoes_ponto verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar correcoes de ponto."
    }

    db.query correcao_ponto {
      where = $db.correcao_ponto.status == "pendente"
      sort = {correcao_ponto.created_at: "asc"}
      return = {type: "list"}
    } as $correcoes_pendentes

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

    var $correcoes_no_escopo {
      value = []
    }

    conditional {
      if ($departamento_escopo_id == null) {
        var.update $correcoes_no_escopo {
          value = $correcoes_pendentes
        }
      }
    }

    conditional {
      if ($departamento_escopo_id != null) {
        foreach ($correcoes_pendentes) {
          each as $correcao_item {
            db.get colaborador {
              field_name = "id"
              field_value = $correcao_item.colaborador_id
            } as $colaborador_da_correcao

            conditional {
              if ($colaborador_da_correcao != null && $colaborador_da_correcao.departamento_id == $departamento_escopo_id) {
                var.update $correcoes_no_escopo {
                  value = $correcoes_no_escopo|push:$correcao_item
                }
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso   : true
    correcoes : $correcoes_no_escopo
  }

  guid = "conectahr-correcoes-ponto-get-0001"
}
