// Cria o ciclo de metas de um ano (change ciclo-de-metas, D1): tres janelas iguais para toda a
// empresa. Um ciclo por ano. So RH e Admin; auditado.
query "ciclos_metas" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int ano
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

    precondition (($input.ano >= 2020) && ($input.ano <= 2100)) {
      error_type = "inputerror"
      error = "Ano invalido."
    }

    var $ano_ciclo {
      value = $input.ano
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

    db.query ciclo_metas {
      where = $db.ciclo_metas.ano == $input.ano
      return = {type: "single"}
    } as $ciclo_existente

    precondition ($ciclo_existente == null) {
      error_type = "inputerror"
      error = "Ja existe um ciclo de metas para este ano."
    }

    db.add ciclo_metas {
      data = {ano: $input.ano, etapa1_inicio: $input.etapa1_inicio, etapa1_fim: $input.etapa1_fim, etapa2_inicio: $input.etapa2_inicio, etapa2_fim: $input.etapa2_fim, etapa3_inicio: $input.etapa3_inicio, etapa3_fim: $input.etapa3_fim, criado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
    } as $ciclo_criado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_ciclo_metas"
        recurso    : "ciclo_metas"
        registro_id: $ciclo_criado.id
        valor_novo : ("ano=" ~ ($input.ano|to_text) ~ "; etapa1=" ~ $input.etapa1_inicio ~ ".." ~ $input.etapa1_fim ~ "; etapa2=" ~ $input.etapa2_inicio ~ ".." ~ $input.etapa2_fim ~ "; etapa3=" ~ $input.etapa3_inicio ~ ".." ~ $input.etapa3_fim)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Ciclo de metas criado."
    ciclo   : $ciclo_criado
  }

  guid = "conectahr-ciclos-metas-post-0001"
}
