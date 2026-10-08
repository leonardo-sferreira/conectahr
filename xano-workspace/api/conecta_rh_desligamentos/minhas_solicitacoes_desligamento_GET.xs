// Lista as solicitações de desligamento criadas
// pela própria conta autenticada.
// Não recebe user_id ou colaborador_id.
query minhas_solicitacoes_desligamento verb=GET {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuário identificado pelo token.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
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
  
    // Contas inativas não podem consultar solicitações.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Esta consulta é destinada a colaboradores e gestores.
    precondition ($perfil_autenticado == "COLABORADOR" || $perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente colaboradores ou gestores podem consultar suas próprias solicitações."
    }
  
    // Confirma que a conta possui um colaborador vinculado.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Não existe um colaborador vinculado à conta autenticada."
    }
  
    // Lista somente solicitações criadas pela própria conta.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.solicitante_user_id == $usuario_autenticado.id
      return = {type: "list"}
    } as $solicitacoes
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $solicitacoes|count
    }
  }

  response = {
    sucesso     : true
    quantidade  : $quantidade
    solicitacoes: $solicitacoes
  }

  guid = "cY6qy2yfmvCbN74aUSFs7McZ_Jk"
}