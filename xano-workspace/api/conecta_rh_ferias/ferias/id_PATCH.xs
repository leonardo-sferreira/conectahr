// Edita uma solicitacao de ferias do usuario autenticado.
// Permite qualquer perfil com colaborador ativo vinculado.
// Somente solicitacoes proprias e pendentes podem ser alteradas.
query "ferias/{id}" verb=PATCH {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    int id
    date data_inicio
    date data_fim
    int quantidade_dias filters=min:1|max:30
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
  
    // Contas inativas nao podem editar solicitacoes.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Localiza o colaborador pelo token.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Somente colaborador profissionalmente ativo
    // pode editar uma solicitacao.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem editar solicitacoes de ferias."
    }
  
    // Localiza a solicitacao.
    db.get ferias {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao
  
    precondition ($solicitacao != null) {
      error_type = "notfound"
      error = "Solicitacao de ferias nao encontrada."
    }
  
    // Impede alteracao de solicitacao pertencente a outra pessoa.
    precondition ($solicitacao.colaborador_id == $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para editar esta solicitacao de ferias."
    }
  
    // Normaliza o status atual.
    var $status_solicitacao {
      value = $solicitacao.status|trim|to_upper
    }
  
    // Somente solicitacoes pendentes podem ser alteradas.
    precondition ($status_solicitacao == "PENDENTE") {
      error_type = "inputerror"
      error = "Somente solicitacoes pendentes podem ser alteradas."
    }
  
    // A data final nao pode ser anterior a data inicial.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }
  
    // Atualiza somente os campos permitidos.
    db.edit ferias {
      field_name = "id"
      field_value = $solicitacao.id
      data = {
        data_inicio    : $input.data_inicio
        data_fim       : $input.data_fim
        quantidade_dias: $input.quantidade_dias
        updated_at     : "now"
      }
    } as $solicitacao_atualizada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao de ferias atualizada com sucesso."
    solicitacao: $solicitacao_atualizada
  }

  guid = "WzTNqKmOyzPMK05sssUtk2Wpraw"
}