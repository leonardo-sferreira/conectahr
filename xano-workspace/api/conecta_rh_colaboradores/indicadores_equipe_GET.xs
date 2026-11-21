// Indicadores do setor do Gestor (change backend-gestor-pendencias, D2): so agregados dos ultimos 6 meses, sem nomes
// nem ids de pessoas, com o setor de menos de 5 pessoas oculto. A folha individual continua com o escopo de sempre.
query indicadores_equipe verb=GET {
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

    precondition ($perfil_autenticado == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente o Gestor ve os indicadores do proprio setor."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
      output = ["id"]
    } as $ficha_gestor

    var $ficha_gestor_id {
      value = ($ficha_gestor != null) ? $ficha_gestor.id : 0
    }

    db.query departamento {
      where = $db.departamento.gestor_colaborador_id == $ficha_gestor_id
      return = {type: "single"}
      output = ["id", "nome"]
    } as $setor_gerido

    precondition ($setor_gerido != null) {
      error_type = "notfound"
      error = "Sua conta nao e gestora de nenhum setor."
    }

    function.run "ConectaHR/indicadores_setor" {
      input = {departamento_id: $setor_gerido.id, excluir_colaborador_id: $ficha_gestor_id, minimo: 5}
    } as $indicadores
  }

  response = {
    sucesso    : true
    indicadores: $indicadores
  }

  guid = "conectahr-indicadores-equipe-get-0001"
}
