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
    text? numero_documento? filters=trim|max:100
    text? estado_de_emissao? filters=trim|max:50
    date? data_emissao?
    date? data_validade?
    image? imagem_frente?
    image? imagem_verso?
    text? arquivo_url? filters=trim|min:10|max:2000
    text? observacao? filters=trim|max:1000
    int? documento_substituido_id?
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

    // Autoriza RH, ADMIN ou o proprio colaborador — checado antes de
    // qualquer estado do colaborador-alvo, para nao revelar esse estado
    // a quem nao tem permissao de acessar o registro.
    precondition ($acesso_administrativo || $acesso_proprietario) {
      error_type = "accessdenied"
      error = "Voce nao possui permissao para cadastrar documentos para este colaborador."
    }

    // Impede cadastro para colaborador desligado.
    var $status_colaborador {
      value = $colaborador_destino.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel cadastrar documento para colaborador desligado."
    }

    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "rg" || $input.tipo == "cpf" || $input.tipo == "cin" || $input.tipo == "cnh" || $input.tipo == "ctps" || $input.tipo == "aso_admissional" || $input.tipo == "laudo_deficiencia" || $input.tipo == "certificado_profissional" || $input.tipo == "comprovante_residencia" || $input.tipo == "comprovante_escolaridade" || $input.tipo == "registro_profissional" || $input.tipo == "documentacao_migratoria" || $input.tipo == "certificado_reservista" || $input.tipo == "documentacao_responsavel_legal" || $input.tipo == "outro" || $input.tipo == "holerite" || $input.tipo == "informe_rendimentos") {
      error_type = "inputerror"
      error = "Tipo de documento invalido."
    }

    // Holerite e informe de rendimentos sao emitidos exclusivamente pelo RH/ADMIN.
    var $emitido_pelo_rh {
      value = ($input.tipo == "holerite" || $input.tipo == "informe_rendimentos")
    }

    precondition ($emitido_pelo_rh == false || $acesso_administrativo) {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem anexar holerite ou informe de rendimentos."
    }

    // Documentos emitidos pelo RH entram ja aprovados, sem data de validade
    // (RH e a fonte da informacao; esses tipos nao vencem).
    var $status_inicial {
      value = ($emitido_pelo_rh ? "aprovado" : "pendente_analise")
    }

    var $data_validade_final {
      value = ($emitido_pelo_rh ? null : $input.data_validade)
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

    // Hash de duplicidade (item 5.1) — so calculavel para arquivo_url
    // (um link, texto estavel); nao ha como calcular hash do conteudo
    // real de imagem_frente/imagem_verso a partir do parametro de
    // entrada nesta camada do Xano (fica como gap documentado, exigiria
    // acesso aos bytes do arquivo, nao exposto ao XanoScript aqui).
    var $hash_arquivo_calculado {
      value = ($input.arquivo_url != null ? ($input.arquivo_url|md5) : null)
    }

    // A coluna documento.estado_de_emissao tem uma restricao NOT NULL na
    // tabela real que a declaracao `?` no schema nao remove (quirk da
    // plataforma) — sem isso, omitir estado_de_emissao quebra o insert
    // com "SQL Error: 23502, NOT NULL VIOLATION".
    var $estado_de_emissao_final {
      value = ($input.estado_de_emissao != null ? $input.estado_de_emissao : "")
    }

    conditional {
      if ($hash_arquivo_calculado != null) {
        db.query documento {
          where = $db.documento.colaborador_id == $colaborador_destino.id && $db.documento.hash_arquivo == $hash_arquivo_calculado && $db.documento.ativo == true
          return = {type: "single"}
        } as $documento_duplicado

        precondition ($documento_duplicado == null) {
          error_type = "inputerror"
          error = "Este arquivo ja foi cadastrado para este colaborador (duplicidade detectada pelo link informado)."
        }
      }
    }

    // Quarentena de arquivos (item 5.7): confere extensao, tamanho e tipo
    // declarado antes de liberar o anexo. Imagens (imagem_frente/verso) ja
    // sao validadas pelo proprio Xano no upload, entao ficam liberadas por
    // construcao — so arquivo_url passa pela verificacao.
    function.run "ConectaHR/verificar_arquivo_documento" {
      input = {arquivo_url: $input.arquivo_url}
    } as $verificacao_arquivo

    // Localiza uma pendencia aberta deste tipo, para encerra-la automaticamente.
    db.query pendencia_documento {
      where = $db.pendencia_documento.colaborador_id == $colaborador_destino.id && $db.pendencia_documento.tipo_documento == $input.tipo && $db.pendencia_documento.status == "pendente"
      return = {type: "single"}
    } as $pendencia_aberta

    // Cadastra o documento e, quando aplicavel, encerra o anterior na mesma transacao.
    db.transaction {
      stack {
        db.add documento {
          data = {
            colaborador_id           : $colaborador_destino.id
            tipo                     : $input.tipo
            nome_documento           : $input.nome_documento
            numero_documento         : $input.numero_documento
            estado_de_emissao        : $estado_de_emissao_final
            data_emissao             : $input.data_emissao
            data_validade            : $data_validade_final
            status                   : $status_inicial
            imagem_frente            : $imagem_frente_final
            imagem_verso             : $imagem_verso_final
            arquivo_url              : $input.arquivo_url
            hash_arquivo             : $hash_arquivo_calculado
            estado_verificacao       : $verificacao_arquivo.estado_verificacao
            motivo_bloqueio          : $verificacao_arquivo.motivo_bloqueio
            observacao               : $input.observacao
            documento_substituido_id : $input.documento_substituido_id
            ativo                    : true
            updated_at               : "now"
          }
        } as $documento_criado

        // Auditoria: cadastro de documento (item 7.11).
        db.add auditoria {
          data = {
            user_id    : $usuario_autenticado.id
            acao       : "cadastrar_documento"
            recurso    : "documento"
            registro_id: $documento_criado.id
            valor_novo : ("tipo=" ~ $input.tipo ~ "; estado_verificacao=" ~ $verificacao_arquivo.estado_verificacao)
            resultado  : "sucesso"
          }
        } as $evento_auditoria

        conditional {
          if ($input.documento_substituido_id != null) {
            db.edit documento {
              field_name = "id"
              field_value = $input.documento_substituido_id
              data = {status: "substituido", updated_at: "now"}
            } as $documento_substituido_atualizado
          }
        }

        conditional {
          if ($pendencia_aberta != null) {
            db.edit pendencia_documento {
              field_name = "id"
              field_value = $pendencia_aberta.id
              data = {
                status                    : "atendida"
                atendida_por_documento_id : $documento_criado.id
                atendida_em               : "now"
                updated_at                : "now"
              }
            } as $pendencia_atendida
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