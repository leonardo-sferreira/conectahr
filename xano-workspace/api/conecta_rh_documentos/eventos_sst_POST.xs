// RH/ADMIN registra um evento de SST (ASO/PCMSO). So o resultado
// operacional (apto/inapto/apto com restricao) e metadados - nunca um
// diagnostico ou prontuario medico em texto livre.
query eventos_sst verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    int colaborador_id
    text tipo filters=trim
    text? resultado? filters=trim
    date data_exame
    date? data_validade?
    text? medico_responsavel? filters=trim|max:200
    text? documento_url? filters=trim|max:500
    text? observacao_operacional? filters=trim|max:300
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem registrar eventos de SST."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Valida o tipo usando os valores exatos do Enum.
    precondition ($input.tipo == "aso_admissional" || $input.tipo == "aso_periodico" || $input.tipo == "aso_demissional" || $input.tipo == "aso_mudanca_funcao" || $input.tipo == "pcmso_prazo" || $input.tipo == "outro_sst") {
      error_type = "inputerror"
      error = "Tipo de evento SST invalido."
    }

    conditional {
      if ($input.resultado != null) {
        precondition ($input.resultado == "apto" || $input.resultado == "inapto" || $input.resultado == "apto_com_restricao") {
          error_type = "inputerror"
          error = "Resultado invalido. Use apto, inapto ou apto_com_restricao."
        }
      }
    }

    db.add evento_sst {
      data = {
        colaborador_id           : $colaborador_alvo.id
        tipo                        : $input.tipo
        resultado                     : $input.resultado
        data_exame                       : $input.data_exame
        data_validade                       : $input.data_validade
        medico_responsavel                     : $input.medico_responsavel
        documento_url                             : $input.documento_url
        observacao_operacional                       : $input.observacao_operacional
        registrado_por_user_id                          : $usuario_autenticado.id
        updated_at                                         : "now"
      }
    } as $evento_criado

    // Auditoria: registro de evento de SST.
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "registrar_evento_sst"
        recurso    : "evento_sst"
        registro_id: $evento_criado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Evento de SST registrado com sucesso."
    evento  : $evento_criado
  }

  guid = "conectahr-eventos-sst-post-0001"
}
