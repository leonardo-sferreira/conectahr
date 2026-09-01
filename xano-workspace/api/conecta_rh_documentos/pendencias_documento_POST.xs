// RH solicita um documento ausente ou vencido, com prazo. Notifica o
// colaborador por e-mail (melhor esforço; falha no envio nao impede a
// criacao da pendencia — mesma filosofia de notificacoes assincronas
// do design.md).
query "pendencias_documento" verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int colaborador_id
    text tipo_documento filters=trim
    date prazo
    text? observacao? filters=trim|max:500
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem solicitar documentos."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $status_colaborador {
      value = $colaborador_alvo.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel solicitar documento para colaborador desligado."
    }

    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo_documento == "rg" || $input.tipo_documento == "cpf" || $input.tipo_documento == "cin" || $input.tipo_documento == "cnh" || $input.tipo_documento == "ctps" || $input.tipo_documento == "aso_admissional" || $input.tipo_documento == "laudo_deficiencia" || $input.tipo_documento == "certificado_profissional" || $input.tipo_documento == "comprovante_residencia" || $input.tipo_documento == "comprovante_escolaridade" || $input.tipo_documento == "registro_profissional" || $input.tipo_documento == "documentacao_migratoria" || $input.tipo_documento == "certificado_reservista" || $input.tipo_documento == "documentacao_responsavel_legal" || $input.tipo_documento == "outro") {
      error_type = "inputerror"
      error = "Tipo de documento invalido."
    }

    // Comparar um `date` diretamente com "now" faz comparacao de texto,
    // nao de data (digitos vem antes de 'n' no ASCII, entao qualquer
    // data "<=" "now" e sempre verdadeiro e "now" nunca e superado) —
    // converte ambos os lados para timestamp numerico antes de comparar.
    var $prazo_ts {
      value = ($input.prazo|to_timestamp)
    }

    var $agora_ts_prazo {
      value = (now|to_timestamp)
    }

    precondition ($prazo_ts >= $agora_ts_prazo) {
      error_type = "inputerror"
      error = "O prazo deve ser uma data futura."
    }

    // Impede pendencia duplicada em aberto para o mesmo tipo.
    db.query pendencia_documento {
      where = $db.pendencia_documento.colaborador_id == $colaborador_alvo.id && $db.pendencia_documento.tipo_documento == $input.tipo_documento && $db.pendencia_documento.status == "pendente"
      return = {type: "single"}
    } as $pendencia_existente

    precondition ($pendencia_existente == null) {
      error_type = "inputerror"
      error = "Ja existe uma pendencia em aberto deste tipo de documento para este colaborador."
    }

    db.add pendencia_documento {
      data = {
        colaborador_id         : $colaborador_alvo.id
        tipo_documento          : $input.tipo_documento
        prazo                   : $input.prazo
        observacao              : $input.observacao
        status                  : "pendente"
        solicitado_por_user_id  : $usuario_autenticado.id
        updated_at              : "now"
      }
    } as $pendencia_criada

    // Notifica o colaborador por e-mail (melhor esforco).
    conditional {
      if ($colaborador_alvo.email_pessoal != null) {
        // Template transacional "conectahr_documento_pendente" (id 5 —
        // ver docs/emails-templates.md).
        api.request {
          url = "https://api.brevo.com/v3/smtp/email"
          method = "POST"
          headers = ["Content-Type: application/json", "api-key: " ~ $env.BREVO_API_KEY]
          params = {
            to        : [{email: $colaborador_alvo.email_pessoal, name: $colaborador_alvo.nome}]
            templateId: 5
            params    : {nome: $colaborador_alvo.nome, tipo_documento: $input.tipo_documento, prazo: ($input.prazo|format_timestamp:"d/m/Y":"UTC")}
          }
        } as $envio_notificacao
      }
    }

    // Auditoria: solicitacao de documento pendente.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "solicitar_documento_pendente"
        recurso    : "pendencia_documento"
        registro_id: $pendencia_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso   : true
    mensagem  : "Pendencia de documento criada e colaborador notificado."
    pendencia : $pendencia_criada
  }

  guid = "conectahr-pendencias-documento-post-0001"
}
