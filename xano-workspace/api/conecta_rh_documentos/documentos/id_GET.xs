// Consulta um documento especifico pelo ID.
// RH e ADMIN podem consultar qualquer registro.
// Outros usuarios podem consultar somente documentos proprios.
query "documentos/{id}" verb=GET {
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
  
    // Normaliza o perfil autenticado.
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
  
    // Define se a conta possui permissao administrativa.
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
  
    // Por padrao, ainda nao existe autorizacao por propriedade.
    var $acesso_proprietario {
      value = false
    }
  
    // Para usuarios sem acesso administrativo,
    // localiza o colaborador pelo token.
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
      
        // Impede consulta por colaborador desligado.
        var $status_colaborador {
          value = $colaborador_autenticado.status|trim|to_upper
        }
      
        precondition ($status_colaborador != "DESLIGADO") {
          error_type = "accessdenied"
          error = "Colaborador desligado nao pode consultar documentos."
        }
      
        // Confere se o documento pertence ao colaborador autenticado.
        conditional {
          if ($documento.colaborador_id == $colaborador_autenticado.id) {
            var.update $acesso_proprietario {
              value = true
            }
          }
        }
      }
    }
  
    // Autoriza RH, ADMIN ou o proprietario do documento.
    precondition ($acesso_administrativo || $acesso_proprietario) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para consultar este documento."
    }
  }

  response = {sucesso: true, documento: $documento}
  guid = "FRIVXh7li4r4-aPN1ejb7QCSb-M"
}