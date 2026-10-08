// Lista somente os documentos do usuario autenticado.
// Nao recebe user_id nem colaborador_id.
// O vinculo e localizado exclusivamente pelo token.
query meus_documentos verb=GET {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuario autenticado.
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
  
    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Localiza o colaborador vinculado ao usuario autenticado.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Impede consulta por colaborador desligado.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "accessdenied"
      error = "Colaborador desligado nao pode consultar documentos."
    }
  
    // Lista somente os documentos do colaborador autenticado.
    db.query documento {
      where = $db.documento.colaborador_id == $colaborador_autenticado.id
      sort = {documento.created_at: "desc"}
      // Sem o arquivo (arquivo_url e imagens): a abertura de arquivo sensivel so acontece em
      // endpoint proprio, que audita cada acesso (LGPD).
      output = ["id", "created_at", "updated_at", "colaborador_id", "tipo", "nome_documento", "numero_documento", "estado_de_emissao", "data_emissao", "data_validade", "retencao_ate", "observacao", "status", "estado_verificacao", "ultimo_alerta_dias", "hash_arquivo", "documento_substituido_id", "motivo_bloqueio", "ativo"]
      return = {type: "list"}
    } as $documentos_encontrados
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $documentos_encontrados|count
    }
  }

  response = {
    sucesso   : true
    quantidade: $quantidade
    documentos: $documentos_encontrados
  }

  guid = "MSa1pvDKluvWrXlRdkFR4b65u64"
}