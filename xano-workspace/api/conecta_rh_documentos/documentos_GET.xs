// Lista os documentos cadastrados no sistema.
// Operacao permitida somente para RH ou ADMIN.
// Nao gera acesso publico aos arquivos armazenados.
query documentos verb=GET {
  api_group = "ConectaRH - Documentos"
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
  
    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem consultar todos os documentos.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar todos os documentos."
    }
  
    // Lista os documentos cadastrados.
    db.query documento {
      sort = {documento.created_at: "desc"}
      return = {type: "list"}
    } as $documentos_encontrados
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $documentos_encontrados|count
    }
  }

  response = {
    sucesso   : true
    quantidade: $quantidade
    documentos: $documentos_encontrados
  }

  guid = "zbFiHs_jqkSFYaAs1cspbN8xhXY"
}