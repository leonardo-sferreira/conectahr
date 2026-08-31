// RH/ADMIN lista as regras cadastradas da matriz de documentos
// obrigatorios (item 5.8).
query documentos_obrigatorios verb=GET {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar a matriz de documentos obrigatorios."
    }

    db.query documento_obrigatorio_regra {
      where = $db.documento_obrigatorio_regra.ativo == true
      sort = {documento_obrigatorio_regra.tipo_documento: "asc"}
      return = {type: "list"}
    } as $regras
  }

  response = {
    sucesso: true
    regras : $regras
  }

  guid = "conectahr-documentos-obrigatorios-get-0001"
}
