// Lista registros de ausencia por status.
// Operacao permitida somente para RH ou ADMIN.
query ausencias verb=GET {
  api_group = "ConectaRH - Ausencias"
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
  
    // Impede consulta por conta inativa.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem listar todas as ausencias.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem listar ausencias."
    }
  
    // Impede filtro vazio.
    precondition ($input.status != "") {
      error_type = "inputerror"
      error = "Informe o status que deseja consultar."
    }
  
    // Lista os registros com o status exato informado.
    db.query ausencia {
      where = $db.ausencia.status == $input.status
      sort = {ausencia.created_at: "desc"}
      return = {type: "list"}
    } as $registros_ausencia
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $registros_ausencia|count
    }
  }

  response = {
    sucesso   : true
    status    : $input.status
    quantidade: $quantidade
    ausencias : $registros_ausencia
  }

  guid = "nejlqda2UnUKYOznpaF0cN4PZy4"
}