// Retorna o espelho de ponto do colaborador autenticado.
// Permite qualquer perfil com colaborador vinculado.
// Diferencia marcacoes originais de ajustes, conforme o status do registro.
query meu_ponto verb=GET {
  api_group = "ConectaRH - Ponto"
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

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Localiza o colaborador vinculado a conta autenticada.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }

    // Lista somente os registros do colaborador autenticado.
    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colaborador_autenticado.id
      sort = {registro_ponto.data: "desc"}
      return = {type: "list"}
    } as $registros_ponto

    // Conta os registros encontrados.
    var $quantidade {
      value = $registros_ponto|count
    }
  }

  response = {
    sucesso   : true
    quantidade: $quantidade
    registros : $registros_ponto
  }

  guid = "conectahr-ponto-meu-ponto-0001"
}
