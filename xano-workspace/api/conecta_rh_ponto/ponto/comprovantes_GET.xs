// Comprovantes de registro de ponto do proprio colaborador (Portaria MTP 671/2021, arts. 79 e
// 80; change ponto-rep-p-e-ferias-clt): as marcacoes dos ultimos 7 dias com os dados que o
// comprovante em PDF precisa. So do proprio usuario: nao recebe id de ninguem.
query "ponto/comprovantes" verb=GET {
  api_group = "ConectaRH - Ponto"
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }

    // Comprovantes dos ultimos 7 dias (a Portaria exige pelo menos 48 horas).
    var $desde {
      value = now - 604800000
    }

    db.query marcacao_ponto {
      where = $db.marcacao_ponto.colaborador_id == $colaborador_autenticado.id && $db.marcacao_ponto.tipo_registro == 7 && $db.marcacao_ponto.data_hora_gravacao >= $desde
      sort = {marcacao_ponto.nsr: "desc"}
      return = {type: "list"}
      output = ["id", "nsr", "data", "data_hora_marcacao", "data_hora_marcacao_txt", "hash"]
    } as $marcacoes

    db.query empregador {
      sort = {empregador.id: "asc"}
      return = {type: "single"}
    } as $empregador

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $colaborador_autenticado.cpf}
    } as $cpf
  }

  response = {
    marcacoes: $marcacoes
    empregador: ($empregador != null ? {razao_social: $empregador.razao_social, tipo_identificador: $empregador.tipo_identificador, identificador: $empregador.identificador, cno_caepf: $empregador.cno_caepf, local_prestacao: $empregador.local_prestacao, inpi_registro: $empregador.inpi_registro} : null)
    trabalhador: {nome: $colaborador_autenticado.nome, cpf: $cpf}
  }

  guid = "conectahr-ponto-comprovantes-get-0001"
}
