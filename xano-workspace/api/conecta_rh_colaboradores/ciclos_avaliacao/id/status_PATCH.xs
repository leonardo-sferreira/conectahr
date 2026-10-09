// RH/ADMIN muda o status de um ciclo de avaliacao. Aceita so as transicoes
// validas (planejamento -> em_andamento -> fechamento -> concluido, e
// cancelado a partir de qualquer estado ainda aberto) e audita a mudanca.
// `metas POST` e `avaliacoes POST` so aceitam ciclo em_andamento.
query "ciclos_avaliacao/{id}/status" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text status filters=trim|lower
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
      error = "Somente RH ou ADMIN podem alterar o status de um ciclo de avaliacao."
    }

    // Tabela de transicoes validas (origem>destino), como texto: evita o problema
    // conhecido do literal de array/objeto em response e permite checar com contains.
    var $transicoes_validas {
      value = ",planejamento>em_andamento,planejamento>cancelado,em_andamento>fechamento,em_andamento>cancelado,fechamento>concluido,fechamento>cancelado,"
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    var $transicao {
      value = ("," ~ $ciclo.status ~ ">" ~ $input.status ~ ",")
    }

    precondition ($transicoes_validas|contains:$transicao) {
      error_type = "inputerror"
      error = "Transicao de status nao permitida para este ciclo."
    }

    db.edit ciclo_avaliacao {
      field_name = "id"
      field_value = $ciclo.id
      data = {
        status    : $input.status
        updated_at: "now"
      }
    } as $ciclo_atualizado

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "alterar_status_ciclo_avaliacao"
        recurso      : "ciclo_avaliacao"
        registro_id  : $ciclo.id
        resultado    : "sucesso"
        justificativa: ($ciclo.status ~ " -> " ~ $input.status)
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Status do ciclo atualizado com sucesso."
    ciclo   : $ciclo_atualizado
  }

  guid = "conectahr-ciclos-avaliacao-status-patch-0001"
}
