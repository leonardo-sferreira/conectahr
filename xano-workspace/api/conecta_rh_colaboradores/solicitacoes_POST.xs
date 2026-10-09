// Colaborador autenticado registra uma solicitacao ao RH (alteracao
// cadastral, declaracao, documento avulso ou outra demanda).
query solicitacoes verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text tipo filters=trim
    text descricao filters=trim|min:5|max:2000
    text? subtipo_lgpd? filters=trim
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
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode registrar solicitacoes."
    }

    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "alteracao_cadastral" || $input.tipo == "declaracao" || $input.tipo == "documento_avulso" || $input.tipo == "outra" || $input.tipo == "privacidade_lgpd") {
      error_type = "inputerror"
      error = "Tipo de solicitacao invalido. Use alteracao_cadastral, declaracao, documento_avulso, outra ou privacidade_lgpd."
    }

    // Pedido LGPD: exige um dos sete subtipos e ganha prazo de resposta de 15 dias.
    // Os outros tipos nao aceitam subtipo.
    var $e_pedido_lgpd {
      value = ($input.tipo == "privacidade_lgpd")
    }

    precondition ($e_pedido_lgpd || $input.subtipo_lgpd == null || $input.subtipo_lgpd == "") {
      error_type = "inputerror"
      error = "O subtipo so se aplica a pedidos de privacidade (privacidade_lgpd)."
    }

    precondition ($e_pedido_lgpd == false || ($input.subtipo_lgpd == "confirmacao_acesso" || $input.subtipo_lgpd == "correcao" || $input.subtipo_lgpd == "anonimizacao_eliminacao" || $input.subtipo_lgpd == "portabilidade" || $input.subtipo_lgpd == "informacao_compartilhamento" || $input.subtipo_lgpd == "revogacao_consentimento" || $input.subtipo_lgpd == "oposicao")) {
      error_type = "inputerror"
      error = "Informe o subtipo do pedido: confirmacao_acesso, correcao, anonimizacao_eliminacao, portabilidade, informacao_compartilhamento, revogacao_consentimento ou oposicao."
    }

    var $prazo_lgpd {
      value = ($e_pedido_lgpd ? (now|add_secs_to_timestamp:1296000|format_timestamp:"Y-m-d":"UTC") : null)
    }

    db.add solicitacao_rh {
      data = {
        colaborador_id: $colaborador_autenticado.id
        tipo          : $input.tipo
        descricao     : $input.descricao
        subtipo_lgpd  : ($e_pedido_lgpd ? $input.subtipo_lgpd : null)
        prazo_resposta: $prazo_lgpd
        status        : "recebida"
        updated_at    : "now"
      }
    } as $solicitacao_criada

    // Auditoria: nova solicitacao ao RH.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_solicitacao_rh"
        recurso    : "solicitacao_rh"
        registro_id: $solicitacao_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitacao registrada com sucesso."
    solicitacao: $solicitacao_criada
  }

  guid = "conectahr-solicitacoes-post-0001"
}
