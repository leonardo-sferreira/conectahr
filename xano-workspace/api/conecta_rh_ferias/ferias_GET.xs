// Lista solicitacoes de ferias.
// Operacao permitida somente para RH ou ADMIN.
// O filtro deve usar o valor exato configurado no Enum de ferias.status.
query ferias verb=GET {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    text status filters=trim
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
  
    // Impede consultas realizadas por contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Normaliza o perfil de acesso.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem listar todas as solicitacoes.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem listar solicitacoes de ferias."
    }
  
    // Impede filtro vazio.
    precondition ($input.status != "") {
      error_type = "inputerror"
      error = "Informe o status que deseja consultar."
    }
  
    // Lista as solicitacoes do status informado.
    db.query ferias {
      where = $db.ferias.status == $input.status
      return = {type: "list"}
    } as $solicitacoes
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $solicitacoes|count
    }
  }

  response = {
    sucesso     : true
    status      : $input.status
    quantidade  : $quantidade
    solicitacoes: $solicitacoes
  }

  guid = "wbn-5OZ5-H-C4oAUKmXxXx9VFuQ"
}