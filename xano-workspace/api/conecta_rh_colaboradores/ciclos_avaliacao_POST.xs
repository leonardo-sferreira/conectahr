// RH/ADMIN cria um ciclo de avaliacao.
query ciclos_avaliacao verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text nome filters=trim|max:100
    text descricao filters=trim|max:500
    date? data_inicio?
    date? data_checkin?
    date? data_fim?
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem criar ciclos de avaliacao."
    }

    db.add ciclo_avaliacao {
      data = {
        nome            : $input.nome
        descricao         : $input.descricao
        data_inicio         : $input.data_inicio
        data_checkin          : $input.data_checkin
        data_fim                : $input.data_fim
        status                    : "planejamento"
        criado_por_user_id          : $usuario_autenticado.id
        ativo                         : true
        updated_at                      : "now"
      }
    } as $ciclo_criado
  }

  response = {
    sucesso : true
    mensagem: "Ciclo de avaliacao criado com sucesso."
    ciclo   : $ciclo_criado
  }

  guid = "conectahr-ciclos-avaliacao-post-0001"
}
