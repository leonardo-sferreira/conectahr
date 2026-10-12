// Altera o beneficio de uma so pessoa (tarefa 85): valor da empresa, desconto, fim e observacao.
// Fica marcado como personalizado quando difere do padrao do catalogo. A pessoa recebe o aviso no
// sino. Somente RH ou Admin, e nunca o proprio.
query "colaborador_beneficios/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    decimal valor_empresa filters=min:0
    decimal desconto_colaborador filters=min:0
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

    db.get colaborador_beneficio {
      field_name = "id"
      field_value = $input.id
    } as $vinculo

    precondition ($vinculo != null && $vinculo.ativo) {
      error_type = "notfound"
      error = "Beneficio da pessoa nao encontrado ou ja encerrado."
    }

    precondition ($input.data_fim == null || $input.data_fim >= $vinculo.data_inicio) {
      error_type = "inputerror"
      error = "O fim precisa ser igual ou depois do inicio."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $vinculo.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo == null || $colaborador_alvo.user_id != $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao pode alterar o proprio beneficio."
    }

    db.get beneficio {
      field_name = "id"
      field_value = $vinculo.beneficio_id
    } as $beneficio

    var $personalizado {
      value = $beneficio == null || $input.valor_empresa != $beneficio.valor_empresa_padrao || $input.desconto_colaborador != $beneficio.desconto_padrao
    }

    db.edit colaborador_beneficio {
      field_name = "id"
      field_value = $vinculo.id
      data = {valor_empresa: $input.valor_empresa, desconto_colaborador: $input.desconto_colaborador, data_fim: $input.data_fim, observacao: $input.observacao, valor_personalizado: $personalizado, updated_at: "now"}
    } as $vinculo_alterado

    db.get colaborador {
      field_name = "id"
      field_value = $vinculo.colaborador_id
    } as $pessoa_aviso

    conditional {
      if ($pessoa_aviso != null && $pessoa_aviso.user_id != null) {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $pessoa_aviso.user_id
            tipo                : "beneficio_atualizado"
            titulo              : "Seu beneficio " ~ ($beneficio != null ? $beneficio.nome : "") ~ " foi alterado"
            mensagem            : "A empresa paga R$ " ~ ($input.valor_empresa|to_text) ~ " e o desconto e de R$ " ~ ($input.desconto_colaborador|to_text) ~ " por mes. Veja em Beneficios."
            recurso             : "beneficio"
            registro_id         : $vinculo.beneficio_id
          }
        } as $aviso_beneficio
      }
    }

    db.add auditoria {
      data = {
        user_id     : $usuario_autenticado.id
        acao        : "alterar_beneficio_pessoa"
        recurso     : "colaborador_beneficio"
        registro_id : $vinculo.id
        valor_antigo: "empresa=" ~ ($vinculo.valor_empresa|to_text) ~ "; desconto=" ~ ($vinculo.desconto_colaborador|to_text)
        valor_novo  : "empresa=" ~ ($input.valor_empresa|to_text) ~ "; desconto=" ~ ($input.desconto_colaborador|to_text)
        resultado   : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso: true
    vinculo: $vinculo_alterado
  }

  guid = "conectahr-colaborador-beneficios-id-patch-0001"
}
