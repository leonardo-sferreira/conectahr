// Lista as sessoes do usuario autenticado (ativas e encerradas), mais
// recentes primeiro. Base para a tela "sessoes e dispositivos".
query "auth/minhas_sessoes" verb=GET {
  api_group = "ConectaRH — Autenticação"
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

    db.query sessao {
      where = $db.sessao.user_id == $usuario_autenticado.id
      sort = {sessao.created_at: "desc"}
      return = {type: "list"}
    } as $sessoes
  }

  response = {
    sucesso : true
    sessoes : $sessoes
  }

  guid = "conectahr-auth-minhas-sessoes-get-0001"
}
