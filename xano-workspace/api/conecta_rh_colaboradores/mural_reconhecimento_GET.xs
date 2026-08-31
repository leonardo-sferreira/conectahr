// Mural publico de reconhecimento: somente registros publicos e
// ativos (nao cancelados/moderados). Feedback privado nunca aparece
// aqui.
query "mural_reconhecimento" verb=GET {
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

    db.query reconhecimento {
      where = $db.reconhecimento.visibilidade == "publico" && $db.reconhecimento.status == "ativo"
      sort = {reconhecimento.created_at: "desc"}
      return = {type: "list"}
    } as $mural
  }

  response = {
    sucesso: true
    mural  : $mural
  }

  guid = "conectahr-mural-reconhecimento-get-0001"
}
