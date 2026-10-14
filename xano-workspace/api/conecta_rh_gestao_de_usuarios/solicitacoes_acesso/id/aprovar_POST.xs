// Aprova o pedido de acesso e troca o perfil da conta na hora (change pedido-de-acesso). So o Admin decide; o pedido precisa estar pendente
// e nao pode ser da propria conta do Admin.
query "solicitacoes_acesso/{id}/aprovar" verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
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

    precondition ($perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente o Admin decide pedidos de alteracao de acesso."
    }

    db.get solicitacao_acesso {
      field_name = "id"
      field_value = $input.id
    } as $pedido

    precondition ($pedido != null) {
      error_type = "notfound"
      error = "Pedido de acesso nao encontrado."
    }

    precondition ($pedido.status == "pendente") {
      error_type = "inputerror"
      error = "Este pedido ja foi decidido."
    }

    precondition ($pedido.usuario_id != $usuario_autenticado.id) {
      error_type = "inputerror"
      error = "Voce nao pode decidir um pedido sobre o proprio acesso."
    }

    db.get user {
      field_name = "id"
      field_value = $pedido.usuario_id
    } as $usuario_alvo

    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "A conta do pedido nao existe mais."
    }

    db.edit user {
      field_name = "id"
      field_value = $usuario_alvo.id
      data = {perfil: $pedido.perfil_solicitado}
    } as $usuario_atualizado

    db.edit solicitacao_acesso {
      field_name = "id"
      field_value = $pedido.id
      data = {status: "aprovada", decidido_por_user_id: $usuario_autenticado.id, data_decisao: "now", updated_at: "now"}
    } as $pedido_decidido

    db.add auditoria {
      data = {
        user_id       : $usuario_autenticado.id
        acao          : "alterar_perfil_usuario"
        recurso       : "user"
        registro_id   : $usuario_alvo.id
        valor_anterior: $usuario_alvo.perfil
        valor_novo    : $pedido.perfil_solicitado
        justificativa : "Pedido de acesso " ~ $pedido.id ~ " aprovado"
        resultado     : "sucesso"
      }
    } as $evento_auditoria

    function.run "ConectaHR/notificar" {
      input = {destinatario_user_id: $pedido.solicitante_user_id, autor_user_id: $usuario_autenticado.id, tipo: "pedido_decidido", titulo: "Pedido de acesso aprovado", mensagem: "O Admin aprovou o perfil " ~ $pedido.perfil_solicitado ~ " para " ~ $usuario_alvo.nome ~ ".", recurso: "solicitacao_acesso", registro_id: $pedido.id}
    } as $aviso_rh

    function.run "ConectaHR/notificar" {
      input = {destinatario_user_id: $usuario_alvo.id, autor_user_id: $usuario_autenticado.id, tipo: "cadastro_atualizado", titulo: "Seu acesso mudou", mensagem: "Seu perfil no ConectaRH agora e " ~ $pedido.perfil_solicitado ~ ". Saia e entre de novo para ver as telas do novo perfil.", recurso: "user", registro_id: $usuario_alvo.id}
    } as $aviso_pessoa
  }

  response = {
    sucesso : true
    mensagem: "Pedido aprovado. O perfil da conta foi trocado."
  }

  guid = "conectahr-solicitacoes-acesso-aprovar-0001"
}
