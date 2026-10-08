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
