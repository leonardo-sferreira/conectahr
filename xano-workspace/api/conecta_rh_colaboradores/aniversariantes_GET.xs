// Lista os colaboradores ativos que fazem aniversario no mes corrente.
// Visivel para qualquer usuario autenticado (informacao social, sem
// dado sensivel): retorna apenas nome e dia/mes, nunca o ano de
// nascimento, para nao revelar idade.
query "colaboradores/aniversariantes" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    // Mes corrente, no formato de dois digitos (ex.: "08").
    var $mes_atual {
      value = now|format_timestamp:"m":"UTC"
    }

    // Colaboradores ativos com data de nascimento informada.
    db.query colaborador {
      where = $db.colaborador.status == "Ativo" && $db.colaborador.data_nascimento != null
      return = {type: "list"}
      output = ["id", "nome", "data_nascimento"]
    } as $candidatos

    var $aniversariantes {
      value = []
    }

    foreach ($candidatos) {
      each as $colaborador_item {
        var $mes_nascimento {
          value = $colaborador_item.data_nascimento|format_timestamp:"m":"UTC"
        }

        conditional {
          if ($mes_nascimento == $mes_atual) {
            var.update $aniversariantes {
              value = $aniversariantes|push:{
                id        : $colaborador_item.id
                nome      : $colaborador_item.nome
                aniversario: ($colaborador_item.data_nascimento|format_timestamp:"d/m":"UTC")
              }
            }
          }
        }
      }
    }
  }

  response = {
    sucesso       : true
    mes           : $mes_atual
    aniversariantes: $aniversariantes
  }

  guid = "conectahr-colaboradores-aniversariantes-get-0001"
}
