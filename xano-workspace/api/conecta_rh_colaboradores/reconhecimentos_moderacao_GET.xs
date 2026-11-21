// Fila de moderação do RH (Figma 291:1374; tarefa 66): os reconhecimentos públicos no mural e os já moderados, com
// os nomes, a competência e, nos moderados, quem moderou e o motivo. Somente RH ou Admin.
query "reconhecimentos_moderacao" verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem moderar reconhecimentos."
    }

    db.query reconhecimento {
      where = $db.reconhecimento.visibilidade == "publico" && $db.reconhecimento.status != "cancelado"
      sort = {reconhecimento.created_at: "desc"}
      return = {type: "list"}
    } as $publicos

    function.run "ConectaHR/enriquecer_reconhecimentos" {
      input = {lista: $publicos}
    } as $publicos_com_nomes
  }

  response = {sucesso: true, reconhecimentos: $publicos_com_nomes}

  guid = "conectahr-reconhecimentos-moderacao-get-0001"
}
