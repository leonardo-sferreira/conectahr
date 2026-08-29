// Lista somente os registros de ferias do usuario autenticado.
// Permite qualquer perfil com colaborador vinculado.
// Nao recebe user_id ou colaborador_id.
query minhas_ferias verb=GET {
  api_group = "ConectaRH — Férias"
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
  
    // Contas inativas nao podem consultar ferias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Localiza o colaborador pela conta autenticada.
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
      error = "Colaborador desligado nao pode consultar ferias."
    }
  
    // Lista somente os registros do colaborador autenticado.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id
      sort = {ferias.data_inicio: "desc"}
      return = {type: "list"}
    } as $registros_ferias
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $registros_ferias|count
    }
  }

  response = {
    sucesso   : true
    quantidade: $quantidade
    ferias    : $registros_ferias
  }

  guid = "IO2L5-wUR7ep2BO0kCPwzctPSXc"
}