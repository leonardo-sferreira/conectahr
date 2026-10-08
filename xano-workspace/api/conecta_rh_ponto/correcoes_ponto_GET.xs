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
