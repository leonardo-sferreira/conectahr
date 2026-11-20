// Cadastra uma competencia de avaliacao (change backend-gestor-pendencias, D1). Entra ativa. Sem ela, o
// formulario das avaliacoes fica vazio e nao ha reconhecimento. Auditado. So RH e Admin.
query competencias_avaliacao verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text nome filters=trim
    text? descricao? filters=trim|max:1000
    text categoria filters=trim|lower
    text nivel filters=trim|lower
    decimal? peso?
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

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin cuidam das competencias de avaliacao."
    }

    precondition ((($input.nome|strlen) >= 3) && (($input.nome|strlen) <= 200)) {
      error_type = "inputerror"
      error = "O nome precisa ter de 3 a 200 caracteres."
    }

    var $descricao_final {
      value = ($input.descricao == null) ? "" : $input.descricao
    }

    var $categoria_agulha {
      value = "," ~ $input.categoria ~ ","
    }

    precondition (",tecnica,comportamental,lideranca,valor_empresa,"|contains:$categoria_agulha) {
      error_type = "inputerror"
      error = "Categoria invalida. Use tecnica, comportamental, lideranca ou valor_empresa."
    }

    var $nivel_agulha {
      value = "," ~ $input.nivel ~ ","
    }

    precondition (",l1,l2,l3,l4,l5,"|contains:$nivel_agulha) {
      error_type = "inputerror"
      error = "Nivel invalido. Use l1, l2, l3, l4 ou l5."
    }

    var $peso_final {
      value = ($input.peso == null) ? 1 : $input.peso
    }

    precondition (($peso_final > 0) && ($peso_final <= 100)) {
      error_type = "inputerror"
      error = "O peso vai de mais de 0 ate 100."
    }

    db.add competencia_avaliacao {
      data = {
        nome      : $input.nome
        descricao : $descricao_final
        categoria : $input.categoria
        nivel     : $input.nivel
        peso      : $peso_final
        ativo     : true
      }
    } as $competencia_criada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_competencia_avaliacao"
        recurso    : "competencia_avaliacao"
        registro_id: $competencia_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Competencia cadastrada."
    competencia: $competencia_criada
  }

  guid = "conectahr-competencias-avaliacao-post-0001"
}
