// Lista os documentos cujo prazo de retencao (`retencao_ate`) ja venceu.
// Somente leitura, para RH ou ADMIN: nao altera, anonimiza nem elimina nada
// (a eliminacao/anonimizacao e uma decisao separada, ver docs/lgpd/retencao.md).
// Nao devolve arquivo, link, imagem nem numero do documento.
query "documentos/retencao_vencida" verb=GET {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
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
  
    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar documentos com retencao vencida."
    }

    var $hoje_retencao {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    db.query documento {
      where = $db.documento.retencao_ate != null && $db.documento.retencao_ate < $hoje_retencao
      sort = {documento.retencao_ate: "asc"}
      return = {type: "list"}
      output = ["id", "colaborador_id", "tipo", "nome_documento", "status", "retencao_ate"]
    } as $documentos_vencidos
  }

  response = {
    sucesso  : true
    total    : ($documentos_vencidos|count)
    documentos: $documentos_vencidos
  }

  guid = "conectahr-documentos-retencao-vencida-get-0001"
}
