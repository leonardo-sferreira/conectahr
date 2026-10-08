// Abre o comprovante (atestado) de uma ausencia: devolve um link temporario
// assinado do arquivo privado e registra o acesso na auditoria
// (acessar_arquivo_documento). RH e ADMIN abrem qualquer comprovante; o
// colaborador, somente o proprio. O Gestor NAO tem acesso: o comprovante e dado
// de saude e ele so ve tipo, periodo e status da ausencia.
query "ausencias/{id}/comprovante" verb=GET {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    int id
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
  
    // Contas inativas nao podem abrir comprovantes.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Localiza o registro de ausencia (o comprovante e lido do registro completo).
    db.get ausencia {
      field_name = "id"
      field_value = $input.id
    } as $registro_ausencia

    precondition ($registro_ausencia != null) {
      error_type = "notfound"
      error = "Registro de ausencia nao encontrado."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $e_o_proprio {
      value = (($colaborador_autenticado != null) && ($registro_ausencia.colaborador_id == $colaborador_autenticado.id))
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para abrir este comprovante."
    }

    precondition ($registro_ausencia.comprovante != null) {
      error_type = "notfound"
      error = "Esta ausencia nao possui comprovante."
    }

    // Link temporario (5 minutos) do arquivo privado.
    storage.sign_private_url {
      pathname = $registro_ausencia.comprovante.path
      ttl = 300
    } as $comprovante_assinado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "acessar_arquivo_documento"
        recurso    : "ausencia"
        registro_id: $registro_ausencia.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria_acesso
  }

  response = {
    sucesso           : true
    ausencia_id       : $registro_ausencia.id
    comprovante_url   : $comprovante_assinado
    expira_em_segundos: 300
  }

  guid = "conectahr-ausencias-comprovante-get-0001"
}
