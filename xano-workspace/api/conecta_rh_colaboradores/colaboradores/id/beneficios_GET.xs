// Beneficios de uma pessoa, ativos e encerrados (tarefa 82). Somente RH ou Admin.
query "colaboradores/{id}/beneficios" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.query colaborador_beneficio {
      where = $db.colaborador_beneficio.colaborador_id == $input.id
      sort = {colaborador_beneficio.data_inicio: "desc"}
      return = {type: "list"}
    } as $vinculos

    var $itens {
      value = []
    }

    foreach ($vinculos) {
      each as $v {
        db.get beneficio {
          field_name = "id"
          field_value = $v.beneficio_id
        } as $b

        var.update $itens {
          value = $itens|push:{id: $v.id, beneficio_id: $v.beneficio_id, nome: ($b != null ? $b.nome : "Beneficio"), tipo: ($b != null ? $b.tipo : "outro"), operadora: ($b != null ? $b.operadora : null), valor_empresa: $v.valor_empresa, desconto_colaborador: $v.desconto_colaborador, data_inicio: $v.data_inicio, data_fim: $v.data_fim, observacao: $v.observacao, ativo: $v.ativo}
        }
      }
    }
  }

  response = {
    sucesso   : true
    beneficios: $itens
  }

  guid = "conectahr-colaboradores-beneficios-get-0001"
}
