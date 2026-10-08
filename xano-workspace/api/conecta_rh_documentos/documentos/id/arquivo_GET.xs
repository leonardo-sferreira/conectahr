// Abre o arquivo de um documento: link externo e/ou links temporarios das imagens
// privadas. Cada abertura gera o evento de auditoria acessar_arquivo_documento.
// Adaptado para o plano gratuito do Xano.
// RH e ADMIN podem acessar qualquer documento.
// Outros usuarios podem acessar somente documentos proprios.
query "documentos/{id}/arquivo" verb=GET {
  api_group = "ConectaRH - Documentos"
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
  
    // Bloqueia contas inativas.
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
  
    // Localiza o documento.
    db.get documento {
      field_name = "id"
      field_value = $input.id
    } as $documento
  
    precondition ($documento != null) {
      error_type = "notfound"
      error = "Documento nao encontrado."
    }
  
    // Define permissao administrativa.
    var $acesso_administrativo {
      value = false
    }
  
    conditional {
      if ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
        var.update $acesso_administrativo {
          value = true
        }
      }
    }
  
    // Define permissao por propriedade.
    var $acesso_proprietario {
      value = false
    }
  
    // Usuarios sem acesso administrativo precisam ser proprietarios.
    conditional {
      if ($acesso_administrativo == false) {
        db.get colaborador {
          field_name = "user_id"
          field_value = $usuario_autenticado.id
        } as $colaborador_autenticado
      
        precondition ($colaborador_autenticado != null) {
          error_type = "notfound"
          error = "Nao existe um colaborador vinculado a conta autenticada."
        }
      
        // Impede acesso por colaborador desligado.
        var $status_colaborador {
          value = $colaborador_autenticado.status|trim|to_upper
        }
      
        precondition ($status_colaborador != "DESLIGADO") {
          error_type = "accessdenied"
          error = "Colaborador desligado nao pode acessar documentos."
        }
      
        // Confere se o documento pertence ao colaborador.
        conditional {
          if ($documento.colaborador_id == $colaborador_autenticado.id) {
            var.update $acesso_proprietario {
              value = true
            }
          }
        }
      }
    }
  
    // Autoriza acesso administrativo ou por propriedade — checado antes de
    // revelar se o documento tem ou nao um arquivo vinculado, para nao
    // vazar esse dado a quem nao tem permissao de acessar o registro.
    precondition ($acesso_administrativo || $acesso_proprietario) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para acessar este arquivo."
    }

    // O documento precisa ter ao menos um arquivo: link externo ou imagem privada.
    var $tem_link {
      value = (($documento.arquivo_url != null) && (($documento.arquivo_url|trim) != ""))
    }

    precondition ($tem_link || $documento.imagem_frente != null || $documento.imagem_verso != null) {
      error_type = "notfound"
      error = "Este documento nao possui um arquivo vinculado."
    }

    var $arquivo_url_normalizado {
      value = ($tem_link ? ($documento.arquivo_url|trim) : null)
    }

    // Imagens privadas: link temporario assinado (5 minutos).
    var $url_imagem_frente {
      value = null
    }

    var $url_imagem_verso {
      value = null
    }

    conditional {
      if ($documento.imagem_frente != null) {
        storage.sign_private_url {
          pathname = $documento.imagem_frente.path
          ttl = 300
        } as $frente_assinada

        var.update $url_imagem_frente {
          value = $frente_assinada
        }
      }
    }

    conditional {
      if ($documento.imagem_verso != null) {
        storage.sign_private_url {
          pathname = $documento.imagem_verso.path
          ttl = 300
        } as $verso_assinado

        var.update $url_imagem_verso {
          value = $verso_assinado
        }
      }
    }

    // Auditoria de leitura: toda abertura de arquivo sensivel e registrada, mesmo
    // quando o acesso e permitido (autor, documento e horario).
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "acessar_arquivo_documento"
        recurso    : "documento"
        registro_id: $documento.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria_acesso
  }

  response = {
    sucesso           : true
    documento_id      : $documento.id
    arquivo_url       : $arquivo_url_normalizado
    imagem_frente_url : $url_imagem_frente
    imagem_verso_url  : $url_imagem_verso
    expira_em_segundos: 300
  }

  guid = "scw4k4guwq5O8of1l0Edqdis3OA"
}