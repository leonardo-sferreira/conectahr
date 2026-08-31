// Atualiza um documento existente.
// RH e ADMIN podem atualizar qualquer documento.
// Outros usuarios podem atualizar somente documentos proprios.
// Imagens e arquivo_url atuais sao preservados quando omitidos.
query "documentos/{id}" verb=PATCH {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int id
    text tipo filters=trim
    text nome_documento filters=trim|min:2|max:150
    text? numero_documento? filters=trim|max:100
    text? estado_de_emissao? filters=trim|max:50
    date? data_emissao?
    date? data_validade?
    image? imagem_frente?
    image? imagem_verso?
    text? arquivo_url? filters=trim|min:10|max:2000
    text? observacao? filters=trim|max:1000
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
    } as $documento_atual
  
    precondition ($documento_atual != null) {
      error_type = "notfound"
      error = "Documento nao encontrado."
    }
  
    // Localiza o colaborador proprietario.
    db.get colaborador {
      field_name = "id"
      field_value = $documento_atual.colaborador_id
    } as $colaborador_proprietario
  
    precondition ($colaborador_proprietario != null) {
      error_type = "notfound"
      error = "Colaborador proprietario do documento nao encontrado."
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
      if ($colaborador_proprietario.user_id == $usuario_autenticado.id) {
        var.update $acesso_proprietario {
          value = true
        }
      }
    }
  
    // Autoriza acesso administrativo ou por propriedade — checado antes de
    // qualquer estado do documento, para nao revelar esse estado a quem
    // nao tem permissao de acessar o registro.
    precondition ($acesso_administrativo || $acesso_proprietario) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para atualizar este documento."
    }

    // Somente documentos ativos podem ser atualizados.
    precondition ($documento_atual.ativo) {
      error_type = "inputerror"
      error = "Documento inativo nao pode ser atualizado."
    }

    // Valida o tipo exato do Enum.
    precondition ($input.tipo == "rg" || $input.tipo == "cpf" || $input.tipo == "cin" || $input.tipo == "cnh" || $input.tipo == "ctps" || $input.tipo == "aso_admissional" || $input.tipo == "laudo_deficiencia" || $input.tipo == "certificado_profissional" || $input.tipo == "comprovante_residencia" || $input.tipo == "comprovante_escolaridade" || $input.tipo == "registro_profissional" || $input.tipo == "documentacao_migratoria" || $input.tipo == "certificado_reservista" || $input.tipo == "documentacao_responsavel_legal" || $input.tipo == "outro") {
      error_type = "inputerror"
      error = "Tipo de documento invalido."
    }
  
    // Valida a ordem das datas.
    precondition ($input.data_emissao == null || $input.data_validade == null || $input.data_validade >= $input.data_emissao) {
      error_type = "inputerror"
      error = "A data de validade nao pode ser anterior a data de emissao."
    }
  
    // Preserva a imagem da frente atual.
    var $imagem_frente_final {
      value = $documento_atual.imagem_frente
    }
  
    // Substitui a imagem da frente quando uma nova for enviada.
    conditional {
      if ($input.imagem_frente != null) {
        storage.create_image {
          value = $input.imagem_frente
          access = "private"
          filename = ""
        } as $nova_imagem_frente
      
        var.update $imagem_frente_final {
          value = $nova_imagem_frente
        }
      }
    }
  
    // Preserva a imagem do verso atual.
    var $imagem_verso_final {
      value = $documento_atual.imagem_verso
    }
  
    // Substitui a imagem do verso quando uma nova for enviada.
    conditional {
      if ($input.imagem_verso != null) {
        storage.create_image {
          value = $input.imagem_verso
          access = "private"
          filename = ""
        } as $nova_imagem_verso
      
        var.update $imagem_verso_final {
          value = $nova_imagem_verso
        }
      }
    }
  
    // Preserva o link atual.
    var $arquivo_url_final {
      value = $documento_atual.arquivo_url
    }
  
    // Substitui o link quando um novo for enviado.
    conditional {
      if ($input.arquivo_url != null) {
        var.update $arquivo_url_final {
          value = $input.arquivo_url
        }
      }
    }
  
    // Preserva a observacao atual.
    var $observacao_final {
      value = $documento_atual.observacao
    }

    // A coluna documento.estado_de_emissao tem uma restricao NOT NULL na
    // tabela real que a declaracao `?` no schema nao remove (quirk da
    // plataforma) — preserva o valor atual em vez de sobrescrever com
    // null quando omitido, evitando "SQL Error: 23502, NOT NULL VIOLATION".
    var $estado_de_emissao_final {
      value = $documento_atual.estado_de_emissao
    }

    conditional {
      if ($input.estado_de_emissao != null) {
        var.update $estado_de_emissao_final {
          value = $input.estado_de_emissao
        }
      }
    }
  
    // Substitui a observacao quando uma nova for enviada.
    conditional {
      if ($input.observacao != null) {
        var.update $observacao_final {
          value = $input.observacao
        }
      }
    }
  
    // O documento deve continuar possuindo imagem ou link.
    precondition ($imagem_frente_final != null || $imagem_verso_final != null || $arquivo_url_final != null) {
      error_type = "inputerror"
      error = "O documento precisa possuir imagem_frente, imagem_verso ou arquivo_url."
    }
  
    // Atualiza somente os campos permitidos.
    db.edit documento {
      field_name = "id"
      field_value = $documento_atual.id
      data = {
        tipo             : $input.tipo
        nome_documento   : $input.nome_documento
        numero_documento : $input.numero_documento
        estado_de_emissao: $estado_de_emissao_final
        data_emissao     : $input.data_emissao
        data_validade    : $input.data_validade
        imagem_frente    : $imagem_frente_final
        imagem_verso     : $imagem_verso_final
        arquivo_url      : $arquivo_url_final
        observacao       : $observacao_final
        updated_at       : "now"
      }
    } as $documento_atualizado
  }

  response = {
    sucesso  : true
    mensagem : "Documento atualizado com sucesso."
    documento: $documento_atualizado
  }

  guid = "qu90-u69mbxuDFT5K5wU25YkPFk"
}