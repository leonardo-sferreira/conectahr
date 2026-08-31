// Colaborador autenticado registra uma solicitacao ao RH (alteracao
// cadastral, declaracao, documento avulso ou outra demanda).
query solicitacoes verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    text tipo filters=trim
    text descricao filters=trim|min:5|max:2000
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
    precondition ($input.tipo == "alteracao_cadastral" || $input.tipo == "declaracao" || $input.tipo == "documento_avulso" || $input.tipo == "outra") {
      error_type = "inputerror"
      error = "Tipo de solicitacao invalido. Use alteracao_cadastral, declaracao, documento_avulso ou outra."
    }

    db.add solicitacao_rh {
      data = {
        colaborador_id: $colaborador_autenticado.id
        tipo          : $input.tipo
        descricao     : $input.descricao
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
