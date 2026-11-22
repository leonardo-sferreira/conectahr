// RH/ADMIN ou Gestor cria uma acao de PDI para um colaborador, com um
// responsavel definido. O Gestor, so para os liderados diretos e para o departamento
// de que e gestor (concluir-metas-pdi-equipe, D2). Auditado; a pessoa e avisada no sino.
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    // Lideranca (decisoes D1 a D4 de concluir-metas-pdi-equipe): liderado direto e a ficha cujo superior e a ficha do
    // autenticado; o departamento conta quando o autenticado e o gestor dele.
    var $id_ficha_autenticada {
      value = ($colaborador_autenticado == null) ? 0 : $colaborador_autenticado.id
    }

    var $e_liderado_direto {
      value = ($colaborador_alvo.superior_colaborador_id != null) && ($colaborador_alvo.superior_colaborador_id == $id_ficha_autenticada) && ($colaborador_alvo.status != "Desligado")
    }

    db.get departamento {
      field_name = "id"
      field_value = $colaborador_alvo.departamento_id
    } as $departamento_alvo

    var $gestor_do_departamento_alvo {
      value = (($departamento_alvo == null) || ($departamento_alvo.ativo == false)) ? 0 : $departamento_alvo.gestor_colaborador_id
    }

    var $e_do_meu_departamento {
      value = ($gestor_do_departamento_alvo != null) && ($gestor_do_departamento_alvo == $id_ficha_autenticada) && ($id_ficha_autenticada != 0) && ($colaborador_alvo.status != "Desligado")
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_liderado_direto || $e_do_meu_departamento) {
      error_type = "accessdenied"
      error = "Voce so pode criar PDI para os seus liderados diretos ou para o seu departamento."
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

    precondition ($ciclo.status == "em_andamento") {
      error_type = "inputerror"
      error = "O ciclo de avaliacao precisa estar em andamento."
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || ($responsavel.id == $usuario_autenticado.id) || (($colaborador_alvo.user_id != null) && ($responsavel.id == $colaborador_alvo.user_id))) {
      error_type = "accessdenied"
      error = "O responsavel precisa ser a propria pessoa ou voce."
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

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_pdi"
        recurso    : "pdi"
        registro_id: $pdi_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria

    function.run "ConectaHR/notificar" {
      input = {colaborador_id: $colaborador_alvo.id, autor_user_id: $usuario_autenticado.id, tipo: "acompanhamento_equipe", titulo: "Nova acao no seu PDI", mensagem: $usuario_autenticado.nome ~ " incluiu \"" ~ $input.titulo ~ "\" no seu plano de desenvolvimento.", recurso: "pdi", registro_id: $pdi_criado.id}
    } as $aviso_pdi
  }

  response = {
    sucesso : true
    mensagem: "Acao de PDI criada com sucesso."
    pdi     : $pdi_criado
  }

  guid = "conectahr-pdi-post-0001"
}
