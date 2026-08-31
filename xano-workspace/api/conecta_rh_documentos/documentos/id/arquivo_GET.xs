// Retorna o link externo do arquivo de um documento.
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

    // Confirma que existe um link cadastrado.
    precondition ($documento.arquivo_url != null) {
      error_type = "notfound"
      error = "Este documento nao possui um arquivo vinculado."
    }

    // Confirma que o link nao esta vazio.
    var $arquivo_url_normalizado {
      value = $documento.arquivo_url|trim
    }

    precondition ($arquivo_url_normalizado != "") {
      error_type = "notfound"
      error = "Este documento nao possui um arquivo vinculado."
    }
  }

  response = {
    sucesso     : true
    documento_id: $documento.id
    arquivo_url : $arquivo_url_normalizado
  }

  guid = "scw4k4guwq5O8of1l0Edqdis3OA"
}