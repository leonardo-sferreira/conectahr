// Cadastra um documento para um colaborador.
// RH e ADMIN podem cadastrar para qualquer colaborador.
// Outros usuarios podem cadastrar somente documentos proprios.
// Pelo menos uma imagem ou arquivo_url deve ser informado.
// Quando documento_substituido_id e informado, o documento anterior
// (aprovado ou vencido) e marcado como substituido nesta mesma operacao.
query documentos verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int colaborador_id
    text tipo filters=trim
    text nome_documento filters=trim|min:2|max:150
    text numero_documento? filters=trim|max:100
    text estado_de_emissao? filters=trim|max:50
    date data_emissao?
    date data_validade?
    image? imagem_frente?
    image? imagem_verso?
    text arquivo_url? filters=trim|min:10|max:2000
    text observacao? filters=trim|max:1000
    int documento_substituido_id?
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
  
    // Normaliza o perfil autenticado.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Localiza o colaborador que recebera o documento.
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_destino
  
    precondition ($colaborador_destino != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }
  
    // Impede cadastro para colaborador desligado.
    var $status_colaborador {
      value = $colaborador_destino.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel cadastrar documento para colaborador desligado."
    }
  
    // Define acesso administrativo.
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
  
    // Define acesso por propriedade.
    var $acesso_proprietario {
      value = false
    }
  
    conditional {
      if ($colaborador_destino.user_id == $usuario_autenticado.id) {
        var.update $acesso_proprietario {
          value = true
        }
      }
    }
  
    // Autoriza RH, ADMIN ou o proprio colaborador.
    precondition ($acesso_administrativo || $acesso_proprietario) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para cadastrar documentos para este colaborador."
    }
  
    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "rg" || $input.tipo == "cpf" || $input.tipo == "cin" || $input.tipo == "cnh" || $input.tipo == "ctps" || $input.tipo == "aso_admissional" || $input.tipo == "laudo_deficiencia" || $input.tipo == "certificado_profissional" || $input.tipo == "comprovante_residencia" || $input.tipo == "comprovante_escolaridade" || $input.tipo == "registro_profissional" || $input.tipo == "documentacao_migratoria" || $input.tipo == "certificado_reservista" || $input.tipo == "documentacao_responsavel_legal" || $input.tipo == "outro") {
      error_type = "inputerror"
      error = "Tipo de documento invalido."
    }
  
    // Exige pelo menos uma imagem ou um link externo.
    precondition ($input.imagem_frente != null || $input.imagem_verso != null || $input.arquivo_url != null) {
      error_type = "inputerror"
      error = "Informe imagem_frente, imagem_verso ou arquivo_url."
    }
  
    // Valida a ordem das datas quando ambas forem informadas.
    precondition ($input.data_emissao == null || $input.data_validade == null || $input.data_validade >= $input.data_emissao) {
      error_type = "inputerror"
      error = "A data de validade nao pode ser anterior a data de emissao."
    }
  
    // Prepara a imagem da frente.
    var $imagem_frente_final {
      value = null
    }
  
    conditional {
      if ($input.imagem_frente != null) {
        storage.create_image {
          value = $input.imagem_frente
          access = "private"
          filename = ""
        } as $imagem_frente_privada
      
        var.update $imagem_frente_final {
          value = $imagem_frente_privada
        }
      }
    }
  
    // Prepara a imagem do verso.
    var $imagem_verso_final {
      value = null
    }
  
    conditional {
      if ($input.imagem_verso != null) {
        storage.create_image {
          value = $input.imagem_verso
          access = "private"
          filename = ""
        } as $imagem_verso_privada
      
        var.update $imagem_verso_final {
          value = $imagem_verso_privada
        }
      }
    }
  
    // Valida o documento substituido, quando informado.
    conditional {
      if ($input.documento_substituido_id != null) {
        db.get documento {
          field_name = "id"
          field_value = $input.documento_substituido_id
        } as $documento_anterior

        precondition ($documento_anterior != null) {
          error_type = "notfound"
          error = "Documento a ser substituido nao encontrado."
        }

        precondition ($documento_anterior.colaborador_id == $colaborador_destino.id) {
          error_type = "inputerror"
          error = "O documento a ser substituido nao pertence a este colaborador."
        }

        precondition ($documento_anterior.status == "aprovado" || $documento_anterior.status == "vencido") {
          error_type = "inputerror"
          error = "Somente documentos aprovados ou vencidos podem ser substituidos."
        }
      }
    }

    // Cadastra o documento e, quando aplicavel, encerra o anterior na mesma transacao.
    db.transaction {
      stack {
        db.add documento {
          data = {
            colaborador_id           : $colaborador_destino.id
            tipo                     : $input.tipo
            nome_documento           : $input.nome_documento
            numero_documento         : $input.numero_documento
            estado_de_emissao        : $input.estado_de_emissao
            data_emissao             : $input.data_emissao
            data_validade            : $input.data_validade
            imagem_frente            : $imagem_frente_final
            imagem_verso             : $imagem_verso_final
            arquivo_url              : $input.arquivo_url
            observacao               : $input.observacao
            documento_substituido_id : $input.documento_substituido_id
            ativo                    : true
            updated_at               : "now"
          }
        } as $documento_criado

        conditional {
          if ($input.documento_substituido_id != null) {
            db.edit documento {
              field_name = "id"
              field_value = $input.documento_substituido_id
              data = {status: "substituido", updated_at: "now"}
            } as $documento_substituido_atualizado
          }
        }
      }
    }
  }

  response = {
    sucesso  : true
    mensagem : "Documento cadastrado com sucesso."
    documento: $documento_criado
  }

  guid = "lRVoyvHBufNkO611lSbqKs7V-vE"
}