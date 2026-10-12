// Retorna o espelho de ponto do colaborador autenticado.
// Permite qualquer perfil com colaborador vinculado.
// Diferencia marcacoes originais de ajustes, conforme o status do registro.
query meu_ponto verb=GET {
  api_group = "ConectaRH - Ponto"
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

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Localiza o colaborador vinculado a conta autenticada.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }

    // Lista somente os registros do colaborador autenticado.
    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colaborador_autenticado.id
      sort = {registro_ponto.data: "desc"}
      return = {type: "list"}
    } as $registros_ponto

    // REP-P: as marcacoes da ARP (com NSR) e os tratamentos do proprio colaborador. O dia em
    // registro_ponto e o resumo; as marcacoes sao a fonte (change ponto-rep-p-e-ferias-clt).
    db.query marcacao_ponto {
      where = $db.marcacao_ponto.colaborador_id == $colaborador_autenticado.id && $db.marcacao_ponto.tipo_registro == 7
      sort = {marcacao_ponto.nsr: "asc"}
      return = {type: "list"}
      output = ["id", "nsr", "data", "data_hora_marcacao", "data_hora_marcacao_txt"]
    } as $marcacoes

    db.query tratamento_ponto {
      where = $db.tratamento_ponto.colaborador_id == $colaborador_autenticado.id
      sort = {tratamento_ponto.id: "asc"}
      return = {type: "list"}
      output = ["id", "data", "tipo", "marcacao_id", "data_hora", "motivo", "correcao_ponto_id", "anula_tratamento_id", "created_at"]
    } as $tratamentos

    // Conta os registros encontrados.
    var $quantidade {
      value = $registros_ponto|count
    }
  }

  response = {
    sucesso   : true
    quantidade: $quantidade
    registros : $registros_ponto
    marcacoes : $marcacoes
    tratamentos: $tratamentos
  }

  guid = "conectahr-ponto-meu-ponto-0001"
}
