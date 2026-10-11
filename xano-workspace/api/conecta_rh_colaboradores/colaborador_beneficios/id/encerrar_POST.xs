// Encerra o beneficio de uma pessoa (tarefa 82). Somente RH ou Admin. Nao apaga: preenche a
// data de fim, desativa e audita; o historico continua visivel.
query "colaborador_beneficios/{id}/encerrar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    date data_fim
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

    precondition ($vinculo != null) {
      error_type = "notfound"
      error = "Beneficio da pessoa nao encontrado."
    }

    precondition ($vinculo.ativo) {
      error_type = "inputerror"
      error = "Este beneficio ja esta encerrado."
    }

    precondition ($input.data_fim >= $vinculo.data_inicio) {
      error_type = "inputerror"
      error = "A data de fim precisa ser igual ou depois do inicio."
    }

    db.edit colaborador_beneficio {
      field_name = "id"
      field_value = $vinculo.id
      data = {data_fim: $input.data_fim, ativo: false, observacao: ($input.observacao != null ? $input.observacao : $vinculo.observacao), encerrado_por_user_id: $usuario_autenticado.id, updated_at: "now"}
    } as $vinculo_encerrado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "encerrar_beneficio"
        recurso    : "colaborador_beneficio"
        registro_id: $vinculo.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    vinculo : $vinculo_encerrado
  }

  guid = "conectahr-colaborador-beneficios-encerrar-post-0001"
}
