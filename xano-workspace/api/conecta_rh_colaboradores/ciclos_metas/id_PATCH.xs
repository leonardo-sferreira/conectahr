// Altera as datas de um ciclo de metas (change ciclo-de-metas, D1). So antes de a etapa 1 abrir:
// depois, todos respondem no mesmo periodo e as datas ficam fixas. So RH e Admin; auditado.
query "ciclos_metas/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    date etapa1_inicio
    date etapa1_fim
    date etapa2_inicio
    date etapa2_fim
    date etapa3_inicio
    date etapa3_fim
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.get ciclo_metas {
      field_name = "id"
      field_value = $input.id
    } as $ciclo_atual

    precondition ($ciclo_atual != null) {
      error_type = "notfound"
      error = "Ciclo de metas nao encontrado."
    }

    precondition ($hoje < $ciclo_atual.etapa1_inicio) {
      error_type = "inputerror"
      error = "A etapa 1 deste ciclo ja comecou: as datas nao podem mais mudar."
    }

    var $ano_ciclo {
      value = $ciclo_atual.ano
    }

    // As datas sao do proprio ano e as etapas vem em ordem, sem sobreposicao.
    var $ano_texto {
      value = $ano_ciclo|to_text
    }

    precondition (($input.etapa1_inicio >= ($ano_texto ~ "-01-01")) && ($input.etapa3_fim <= ($ano_texto ~ "-12-31"))) {
      error_type = "inputerror"
      error = "As datas das tres etapas precisam ser do ano do ciclo."
    }

    precondition (($input.etapa1_inicio <= $input.etapa1_fim) && ($input.etapa2_inicio <= $input.etapa2_fim) && ($input.etapa3_inicio <= $input.etapa3_fim)) {
      error_type = "inputerror"
      error = "Em cada etapa, o fim precisa ser igual ou depois do inicio."
    }

    precondition (($input.etapa1_fim < $input.etapa2_inicio) && ($input.etapa2_fim < $input.etapa3_inicio)) {
      error_type = "inputerror"
      error = "Cada etapa precisa comecar depois do fim da anterior."
    }

    db.edit ciclo_metas {
      field_name = "id"
      field_value = $ciclo_atual.id
      data = {etapa1_inicio: $input.etapa1_inicio, etapa1_fim: $input.etapa1_fim, etapa2_inicio: $input.etapa2_inicio, etapa2_fim: $input.etapa2_fim, etapa3_inicio: $input.etapa3_inicio, etapa3_fim: $input.etapa3_fim, updated_at: "now"}
    } as $ciclo_alterado

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "alterar_ciclo_metas"
        recurso       : "ciclo_metas"
        registro_id   : $ciclo_atual.id
        valor_anterior: ("etapa1=" ~ $ciclo_atual.etapa1_inicio ~ ".." ~ $ciclo_atual.etapa1_fim ~ "; etapa2=" ~ $ciclo_atual.etapa2_inicio ~ ".." ~ $ciclo_atual.etapa2_fim ~ "; etapa3=" ~ $ciclo_atual.etapa3_inicio ~ ".." ~ $ciclo_atual.etapa3_fim)
        valor_novo    : ("etapa1=" ~ $input.etapa1_inicio ~ ".." ~ $input.etapa1_fim ~ "; etapa2=" ~ $input.etapa2_inicio ~ ".." ~ $input.etapa2_fim ~ "; etapa3=" ~ $input.etapa3_inicio ~ ".." ~ $input.etapa3_fim)
        resultado     : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Datas do ciclo alteradas."
    ciclo   : $ciclo_alterado
  }

  guid = "conectahr-ciclos-metas-id-patch-0001"
}
