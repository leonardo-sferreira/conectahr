// Vincula um beneficio do catalogo a uma pessoa (tarefa 82). Somente RH ou Admin. O
// beneficio precisa estar ativo, a pessoa nao pode estar desligada e nao pode haver outro
// vinculo vigente do mesmo beneficio para ela.
query "colaboradores/{id}/beneficios" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int beneficio_id
    decimal valor_empresa filters=min:0
    decimal desconto_colaborador filters=min:0
    date data_inicio
    date? data_fim?
    text? observacao? filters=trim|max:500
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
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    precondition (($colaborador_alvo.status|trim|to_upper) != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel vincular beneficio a um colaborador desligado."
    }

    db.get beneficio {
      field_name = "id"
      field_value = $input.beneficio_id
    } as $beneficio

    precondition ($beneficio != null && $beneficio.ativo) {
      error_type = "inputerror"
      error = "Beneficio nao encontrado ou desativado."
    }

    precondition ($input.data_fim == null || $input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim precisa ser igual ou depois do inicio."
    }

    db.query colaborador_beneficio {
      where = $db.colaborador_beneficio.colaborador_id == $input.id && $db.colaborador_beneficio.beneficio_id == $input.beneficio_id && $db.colaborador_beneficio.ativo == true
      return = {type: "single"}
    } as $vigente

    precondition ($vigente == null) {
      error_type = "inputerror"
      error = "A pessoa ja tem este beneficio vigente. Encerre o atual antes de vincular de novo."
    }

    db.add colaborador_beneficio {
      data = {
        colaborador_id       : $input.id
        beneficio_id         : $input.beneficio_id
        valor_empresa        : $input.valor_empresa
        desconto_colaborador : $input.desconto_colaborador
        data_inicio          : $input.data_inicio
        data_fim             : $input.data_fim
        observacao           : $input.observacao
        ativo                : true
        valor_personalizado  : $input.valor_empresa != $beneficio.valor_empresa_padrao || $input.desconto_colaborador != $beneficio.desconto_padrao
        criado_por_user_id   : $usuario_autenticado.id
        updated_at           : "now"
      }
    } as $vinculo_criado

    db.get colaborador {
      field_name = "id"
      field_value = $vinculo_criado.colaborador_id
    } as $pessoa_aviso

    conditional {
      if ($pessoa_aviso != null && $pessoa_aviso.user_id != null) {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $pessoa_aviso.user_id
            tipo                : "beneficio_atualizado"
            titulo              : "Voce tem um novo beneficio: " ~ $beneficio.nome
            mensagem            : "O RH incluiu o beneficio " ~ $beneficio.nome ~ " a partir de " ~ ($input.data_inicio|to_text) ~ ". Veja como usar em Beneficios."
            recurso             : "beneficio"
            registro_id         : $vinculo_criado.beneficio_id
          }
        } as $aviso_beneficio
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "vincular_beneficio"
        recurso    : "colaborador_beneficio"
        registro_id: $vinculo_criado.id
        valor_novo : "colaborador_id=" ~ ($input.id|to_text) ~ "; beneficio_id=" ~ ($input.beneficio_id|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    vinculo : $vinculo_criado
  }

  guid = "conectahr-colaboradores-beneficios-post-0001"
}
