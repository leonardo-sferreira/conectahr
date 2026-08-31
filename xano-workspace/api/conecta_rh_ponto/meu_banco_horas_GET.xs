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
