// Reconhecimentos enviados pela pessoa autenticada (aba "Enviados", Figma 291:908; tarefa 66), públicos e privados,
// com a moderação e o motivo, que quem enviou pode ver. Com os nomes e a competência.
query "meus_reconhecimentos_enviados" verb=GET {
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

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    db.query reconhecimento {
      where = $db.reconhecimento.remetente_user_id == $usuario_autenticado.id && $db.reconhecimento.status != "cancelado"
      sort = {reconhecimento.created_at: "desc"}
      return = {type: "list"}
    } as $enviados

    function.run "ConectaHR/enriquecer_reconhecimentos" {
      input = {lista: $enviados}
    } as $enviados_com_nomes
  }

  response = {sucesso: true, enviados: $enviados_com_nomes}

  guid = "conectahr-meus-reconhecimentos-enviados-get-0001"
}
