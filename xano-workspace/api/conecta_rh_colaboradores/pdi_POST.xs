// RH/ADMIN ou Gestor cria uma acao de PDI para um colaborador, com um
// responsavel definido.
query pdi verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int colaborador_id
    int ciclo_avaliacao_id
    text titulo filters=trim|max:150
    text descricao filters=trim|max:2000
    text acao_desenvolvimento filters=trim|max:2000
    int responsavel_user_id
    date? data_inicio?
    date? data_prazo?
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

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente RH, ADMIN ou Gestor podem criar acoes de PDI."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    db.get ciclo_avaliacao {
      field_name = "id"
      field_value = $input.ciclo_avaliacao_id
    } as $ciclo

    precondition ($ciclo != null) {
      error_type = "notfound"
      error = "Ciclo de avaliacao nao encontrado."
    }

    db.get user {
      field_name = "id"
      field_value = $input.responsavel_user_id
    } as $responsavel

    precondition ($responsavel != null) {
      error_type = "notfound"
      error = "Responsavel nao encontrado."
    }

    db.add pdi {
      data = {
        ciclo_avaliacao_id      : $ciclo.id
        colaborador_id            : $colaborador_alvo.id
        titulo                       : $input.titulo
        descricao                       : $input.descricao
        acao_desenvolvimento               : $input.acao_desenvolvimento
        responsavel_user_id                    : $responsavel.id
        data_inicio                                : $input.data_inicio
        data_prazo                                     : $input.data_prazo
        progresso_percentual                              : 0
        status                                                : "planejado"
        updated_at                                                : "now"
      }
    } as $pdi_criado
  }

  response = {
    sucesso : true
    mensagem: "Acao de PDI criada com sucesso."
    pdi     : $pdi_criado
  }

  guid = "conectahr-pdi-post-0001"
}
