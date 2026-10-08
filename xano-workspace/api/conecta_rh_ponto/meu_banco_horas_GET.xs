// Consulta o proprio saldo de banco de horas e o extrato de lancamentos.
query "meu_banco_horas" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.query banco_horas_lancamento {
      where = $db.banco_horas_lancamento.colaborador_id == $colaborador_autenticado.id
      sort = {banco_horas_lancamento.data_lancamento: "desc"}
      return = {type: "list"}
    } as $lancamentos

    var $saldo {
      value = 0
    }

    foreach ($lancamentos) {
      each as $lancamento_item {
        conditional {
          if ($lancamento_item.tipo == "credito") {
            var.update $saldo {
              value = $saldo + $lancamento_item.horas
            }
          }
        }

        conditional {
          if ($lancamento_item.tipo == "debito") {
            var.update $saldo {
              value = $saldo - $lancamento_item.horas
            }
          }
        }
      }
    }
  }

  response = {
    sucesso     : true
    saldo_horas : $saldo
    lancamentos : $lancamentos
  }

  guid = "conectahr-meu-banco-horas-get-0001"
}
