// Consulta um registro de ferias pelo ID.
// RH e ADMIN consultam qualquer registro.
// Colaborador e Gestor consultam somente registros proprios.
query "ferias/{id}" verb=GET {
  api_group = "ConectaRH — Férias"
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
  
    // Contas inativas nao podem consultar ferias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Localiza o registro de ferias.
    db.get ferias {
      field_name = "id"
      field_value = $input.id
    } as $registro_ferias
  
    precondition ($registro_ferias != null) {
      error_type = "notfound"
      error = "Registro de ferias nao encontrado."
    }
  
    // Localiza o colaborador relacionado ao registro.
    db.get colaborador {
      field_name = "id"
      field_value = $registro_ferias.colaborador_id
    } as $colaborador_registro
  
    precondition ($colaborador_registro != null) {
      error_type = "notfound"
      error = "Colaborador relacionado ao registro de ferias nao encontrado."
    }
  
    // Procura o colaborador vinculado ao usuario autenticado.
    // RH ou ADMIN podem nao possuir esse vinculo.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    // RH e ADMIN consultam qualquer registro.
    // Outros perfis consultam apenas registros proprios.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || ($colaborador_autenticado != null && $registro_ferias.colaborador_id == $colaborador_autenticado.id)) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para consultar este registro de ferias."
    }
  }

  response = {
    sucesso    : true
    ferias     : $registro_ferias
    colaborador: $colaborador_registro
  }

  guid = "22m6cItALT0jcRg9B2tiu3OcUto"
}