// Lista registros de ponto de um colaborador especifico.
// Operacao permitida somente para RH ou ADMIN.
query ponto verb=GET {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int colaborador_id
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

    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    // Somente RH ou ADMIN podem consultar o ponto de outro colaborador.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar o ponto de colaboradores."
    }

    // Confirma que o colaborador informado existe.
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_consultado

    precondition ($colaborador_consultado != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Lista os registros do colaborador informado.
    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colaborador_consultado.id
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

  guid = "conectahr-ponto-listar-0001"
}
