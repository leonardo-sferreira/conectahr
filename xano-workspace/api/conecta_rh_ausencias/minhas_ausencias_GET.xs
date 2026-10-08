// Lista somente as ausencias do usuario autenticado.
// Permite qualquer perfil com colaborador vinculado.
// Nao recebe user_id ou colaborador_id.
query minhas_ausencias verb=GET {
  api_group = "ConectaRH - Ausencias"
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
  
    // Contas inativas nao podem consultar ausencias.
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
  
    // Impede consulta por colaborador desligado.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode consultar ausencias."
    }
  
    // Lista somente as ausencias do colaborador autenticado.
    db.query ausencia {
      where = $db.ausencia.colaborador_id == $colaborador_autenticado.id
      sort = {ausencia.created_at: "desc"}
      // Sem o comprovante (atestado): so abre por ausencias/{id}/comprovante, que audita o acesso.
      output = ["id", "created_at", "updated_at", "colaborador_id", "tipo", "data_inicio", "data_fim", "motivo", "status", "observacao"]
      return = {type: "list"}
    } as $registros_ausencia
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $registros_ausencia|count
    }
  }

  response = {
    sucesso   : true
    quantidade: $quantidade
    ausencias : $registros_ausencia
  }

  guid = "J7ssv6vVvaJBRZL_JJ3kOpEDJMs"
}