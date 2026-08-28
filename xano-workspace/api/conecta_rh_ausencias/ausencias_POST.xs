// Cria uma solicitacao de ausencia para o usuario autenticado.
// Permite comprovante e observacao opcionais.
// Nao recebe colaborador_id ou user_id.
query ausencias verb=POST {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    text tipo filters=trim
    date data_inicio
    date data_fim
    text motivo filters=trim|min:5|max:1000
    attachment? comprovante?
    text observacao? filters=trim|max:1000
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
  
    // Contas inativas nao podem criar ausencias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }
  
    // Localiza o colaborador pelo token.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Somente colaborador profissionalmente ativo
    // pode criar uma solicitacao.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem registrar ausencias."
    }
  
    // Valida o periodo.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }
  
    // Valida o tipo conforme o Enum da tabela.
    precondition ($input.tipo == "Falta" || $input.tipo == "Atestado" || $input.tipo == "Afastamento" || $input.tipo == "Licenca" || $input.tipo == "Outro") {
      error_type = "inputerror"
      error = "Tipo invalido. Use Falta, Atestado, Afastamento, Licenca ou Outro."
    }
  
    // Prepara o comprovante opcional.
    var $comprovante_metadata {
      value = null
    }
  
    // Armazena o arquivo como privado quando enviado.
    conditional {
      if ($input.comprovante != null) {
        storage.create_attachment {
          value = $input.comprovante
          access = "private"
          filename = ""
        } as $arquivo_privado
      
        var.update $comprovante_metadata {
          value = $arquivo_privado
        }
      }
    }
  
    // Cria a solicitacao.
    db.add ausencia {
      data = {
        colaborador_id: $colaborador_autenticado.id
        tipo          : $input.tipo
        data_inicio   : $input.data_inicio
        data_fim      : $input.data_fim
        motivo        : $input.motivo
        comprovante   : $comprovante_metadata
        status        : "Pendente"
        observacao    : $input.observacao
        updated_at    : "now"
      }
    } as $ausencia_criada
  }

  response = {
    sucesso : true
    mensagem: "Solicitacao de ausencia criada com sucesso e enviada para analise."
    ausencia: $ausencia_criada
  }

  guid = "IGyrP5wYk0dFAOKGhL_AkayBL1s"
}