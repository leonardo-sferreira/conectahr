// Lista os artigos de FAQ ativos, para consulta por qualquer usuario
// autenticado.
query artigos_faq verb=GET {
  api_group = "ConectaRH — Colaboradores"
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

    db.query artigo_faq {
      where = $db.artigo_faq.ativo == true
      sort = {artigo_faq.categoria: "asc"}
      return = {type: "list"}
    } as $artigos
  }

  response = {
    sucesso: true
    artigos: $artigos
  }

  guid = "conectahr-artigos-faq-get-0001"
}
