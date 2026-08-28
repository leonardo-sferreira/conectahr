// Cria uma solicitacao de ferias para o usuario autenticado.
// Permite qualquer perfil com colaborador ativo vinculado.
// Nao recebe colaborador_id ou user_id.
query "ferias/solicitacoes" verb=POST {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
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
  
    // Contas inativas nao podem solicitar ferias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
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
    // pode criar uma solicitacao.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem solicitar ferias."
    }
  
    // A data final nao pode ser anterior a data inicial.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }
  
    // Verifica se ja existe uma solicitacao pendente.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && $db.ferias.status == "Pendente"
      return = {type: "single"}
    } as $solicitacao_pendente
  
    precondition ($solicitacao_pendente == null) {
      error_type = "inputerror"
      error = "Ja existe uma solicitacao de ferias pendente para este colaborador."
    }
  
    // Cria a solicitacao com o status exato do Enum.
    db.add ferias {
      data = {
        colaborador_id  : $colaborador_autenticado.id
        data_solicitacao: "now"
        data_inicio     : $input.data_inicio
        data_fim        : $input.data_fim
        quantidade_dias : $input.quantidade_dias
        status          : "Pendente"
        updated_at      : "now"
      }
    } as $solicitacao_criada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao de ferias criada com sucesso e enviada para analise."
    solicitacao: $solicitacao_criada
  }

  guid = "ptQRsxyItifAF-IRd7jxeFPRPes"
}