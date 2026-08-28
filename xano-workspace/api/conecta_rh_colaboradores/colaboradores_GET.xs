// Lista os colaboradores cadastrados.
// Operacao permitida somente para RH ou ADMIN.
// Os registros incluem nivel e nivel_desde.
// Nao consulta nem retorna a senha da tabela user.
query colaboradores verb=GET {
  api_group = "ConectaRH — Colaboradores"
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
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem listar todos os colaboradores.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar colaboradores."
    }
  
    // Lista os colaboradores em ordem alfabetica.
    // Como o registro completo e retornado, nivel e nivel_desde
    // sao incluidos automaticamente.
    db.query colaborador {
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
    } as $colaboradores
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $colaboradores|count
    }
  }

  response = {
    sucesso      : true
    quantidade   : $quantidade
    colaboradores: $colaboradores
  }

  guid = "l_8meofUYauJKvQsO2YdvmM5i9Y"
}