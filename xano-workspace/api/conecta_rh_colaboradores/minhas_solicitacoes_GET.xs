// Central de solicitacoes do colaborador (item 8.1): exibe as proprias
// solicitacoes ao RH (alteracao cadastral, declaracao, documento
// avulso, outra) e, na mesma consulta, o status das suas ferias e
// ausencias — sem duplicar esses fluxos, so agregando a leitura
// (Requirement: Central de solicitacoes do colaborador, cenario
// "Central unificada"). Correcao de ponto (item 4.2) entra aqui quando
// existir.
query "minhas_solicitacoes" verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.query solicitacao_rh {
      where = $db.solicitacao_rh.colaborador_id == $colaborador_autenticado.id
      sort = {solicitacao_rh.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_solicitacoes_rh

    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id
      sort = {ferias.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_ferias

    db.query ausencia {
      where = $db.ausencia.colaborador_id == $colaborador_autenticado.id
      sort = {ausencia.created_at: "desc"}
      return = {type: "list"}
    } as $minhas_ausencias
  }

  response = {
    sucesso    : true
    solicitacoes: $minhas_solicitacoes_rh
    ferias      : $minhas_ferias
    ausencias   : $minhas_ausencias
  }

  guid = "conectahr-minhas-solicitacoes-get-0001"
}
