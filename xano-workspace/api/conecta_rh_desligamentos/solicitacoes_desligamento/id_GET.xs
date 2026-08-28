// Consulta uma solicitação de desligamento específica.
// RH consulta qualquer solicitação.
// O solicitante consulta a própria solicitação.
// Gestor consulta solicitações de departamentos sob sua gestão.
query "solicitacoes_desligamento/{id}" verb=GET {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int id
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado
  
    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
    }
  
    // Contas inativas não podem consultar solicitações.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }
  
    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Localiza a solicitação.
    db.get solicitacao_desligamento {
      field_name = "id"
      field_value = $input.id
    } as $solicitacao
  
    precondition ($solicitacao != null) {
      error_type = "notfound"
      error = "Solicitação de desligamento não encontrada."
    }
  
    // Localiza o colaborador relacionado à solicitação.
    db.get colaborador {
      field_name = "id"
      field_value = $solicitacao.colaborador_id
    } as $colaborador_alvo
  
    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "O colaborador relacionado à solicitação não foi encontrado."
    }
  
    // Localiza o departamento do colaborador.
    db.get departamento {
      field_name = "id"
      field_value = $colaborador_alvo.departamento_id
    } as $departamento_alvo
  
    precondition ($departamento_alvo != null) {
      error_type = "notfound"
      error = "O departamento relacionado à solicitação não foi encontrado."
    }
  
    // Procura o colaborador vinculado à conta autenticada.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    // Verifica se o usuário criou a solicitação.
    var $e_solicitante {
      value = $solicitacao.solicitante_user_id == $usuario_autenticado.id
    }
  
    // Verifica se é o gestor responsável pelo departamento.
    // A expressão precisa permanecer em uma única linha.
    var $e_gestor_responsavel {
      value = ($perfil_autenticado == "GESTOR" && $colaborador_autenticado != null && $departamento_alvo.gestor_colaborador_id == $colaborador_autenticado.id)
    }
  
    // Aplica as permissões.
    precondition ($perfil_autenticado == "RH" || $e_solicitante || $e_gestor_responsavel) {
      error_type = "accessdenied"
      error = "Você não possui permissão para consultar esta solicitação."
    }
  }

  response = {
    sucesso     : true
    solicitacao : $solicitacao
    colaborador : $colaborador_alvo
    departamento: $departamento_alvo
  }

  guid = "dLSP_lnlkzi-sAOtxWkoVSeiNIE"
}