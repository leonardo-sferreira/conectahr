// Consulta um registro de ausencia pelo ID.
// RH e ADMIN consultam qualquer registro.
// Outros usuarios consultam somente registros proprios.
query "ausencias/{id}" verb=GET {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
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
  
    // Contas inativas nao podem consultar ausencias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Localiza o registro de ausencia.
    db.get ausencia {
      field_name = "id"
      field_value = $input.id
    } as $registro_ausencia
  
    precondition ($registro_ausencia != null) {
      error_type = "notfound"
      error = "Registro de ausencia nao encontrado."
    }
  
    // Localiza o colaborador relacionado.
    db.get colaborador {
      field_name = "id"
      field_value = $registro_ausencia.colaborador_id
    } as $colaborador_registro
  
    precondition ($colaborador_registro != null) {
      error_type = "notfound"
      error = "Colaborador relacionado ao registro de ausencia nao encontrado."
    }
  
    // Procura o colaborador vinculado a conta autenticada.
    // RH ou ADMIN podem nao possuir esse vinculo.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    // RH e ADMIN consultam qualquer registro.
    // Outros usuarios consultam somente registros proprios.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || ($colaborador_autenticado != null && $registro_ausencia.colaborador_id == $colaborador_autenticado.id)) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para consultar este registro de ausencia."
    }
  }

  response = {
    sucesso    : true
    ausencia   : $registro_ausencia
    colaborador: $colaborador_registro
  }

  guid = "_ysNVQfe1UHLqNuOoXFl3vS3FiY"
}