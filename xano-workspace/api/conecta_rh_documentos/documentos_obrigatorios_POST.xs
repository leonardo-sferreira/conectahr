// RH/ADMIN cadastra uma regra da matriz de documentos obrigatorios,
// incluindo a politica de retencao aplicavel a esse tipo (item 5.8).
query documentos_obrigatorios verb=POST {
  api_group = "ConectaRH - Documentos"
  auth = "user"

  input {
    text tipo_documento filters=trim
    text? tipo_contrato? filters=trim
    int? cargo_id?
    int? departamento_id?
    int? idade_minima?
    int? idade_maxima?
    text? nacionalidade? filters=trim|max:100
    text? condicao_profissional? filters=trim|max:200
    bool? exige_frente_verso?
    int? prazo_dias_para_envio?
    bool? obrigatorio?
    text? retencao_finalidade? filters=trim|max:500
    text? retencao_base_legal? filters=trim|max:500
    int? retencao_prazo_dias?
    text? retencao_evento_inicial? filters=trim
    text? retencao_tratamento? filters=trim
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem cadastrar regras da matriz de documentos obrigatorios."
    }

    precondition ($input.tipo_documento == "rg" || $input.tipo_documento == "cpf" || $input.tipo_documento == "cin" || $input.tipo_documento == "cnh" || $input.tipo_documento == "ctps" || $input.tipo_documento == "aso_admissional" || $input.tipo_documento == "laudo_deficiencia" || $input.tipo_documento == "certificado_profissional" || $input.tipo_documento == "comprovante_residencia" || $input.tipo_documento == "comprovante_escolaridade" || $input.tipo_documento == "registro_profissional" || $input.tipo_documento == "documentacao_migratoria" || $input.tipo_documento == "certificado_reservista" || $input.tipo_documento == "documentacao_responsavel_legal" || $input.tipo_documento == "outro") {
      error_type = "inputerror"
      error = "Tipo de documento invalido."
    }

    var $tipo_contrato_normalizado {
      value = ($input.tipo_contrato != null ? ($input.tipo_contrato|trim|to_upper) : null)
    }

    precondition ($tipo_contrato_normalizado == null || $tipo_contrato_normalizado == "CLT" || $tipo_contrato_normalizado == "PJ" || $tipo_contrato_normalizado == "ESTAGIO" || $tipo_contrato_normalizado == "APRENDIZ" || $tipo_contrato_normalizado == "TEMPORARIO" || $tipo_contrato_normalizado == "OUTRO") {
      error_type = "inputerror"
      error = "Tipo de contrato invalido."
    }

    var $retencao_evento_normalizado {
      value = ($input.retencao_evento_inicial != null ? ($input.retencao_evento_inicial|trim|to_lower) : null)
    }

    precondition ($retencao_evento_normalizado == null || $retencao_evento_normalizado == "data_emissao" || $retencao_evento_normalizado == "data_validade" || $retencao_evento_normalizado == "desligamento") {
      error_type = "inputerror"
      error = "Evento inicial de retencao invalido."
    }

    var $retencao_tratamento_normalizado {
      value = ($input.retencao_tratamento != null ? ($input.retencao_tratamento|trim|to_lower) : null)
    }

    precondition ($retencao_tratamento_normalizado == null || $retencao_tratamento_normalizado == "anonimizar" || $retencao_tratamento_normalizado == "eliminar_automatico" || $retencao_tratamento_normalizado == "revisao_manual" || $retencao_tratamento_normalizado == "bloqueio_processo") {
      error_type = "inputerror"
      error = "Tratamento de retencao invalido."
    }

    var $obrigatorio_final {
      value = ($input.obrigatorio != null ? $input.obrigatorio : true)
    }

    db.add documento_obrigatorio_regra {
      data = {
        tipo_documento          : $input.tipo_documento
        tipo_contrato           : $tipo_contrato_normalizado
        cargo_id                : $input.cargo_id
        departamento_id         : $input.departamento_id
        idade_minima            : $input.idade_minima
        idade_maxima            : $input.idade_maxima
        nacionalidade           : $input.nacionalidade
        condicao_profissional   : $input.condicao_profissional
        exige_frente_verso      : $input.exige_frente_verso
        prazo_dias_para_envio   : $input.prazo_dias_para_envio
        obrigatorio             : $obrigatorio_final
        retencao_finalidade     : $input.retencao_finalidade
        retencao_base_legal     : $input.retencao_base_legal
        retencao_prazo_dias     : $input.retencao_prazo_dias
        retencao_evento_inicial : $retencao_evento_normalizado
        retencao_tratamento     : $retencao_tratamento_normalizado
        criado_por_user_id      : $usuario_autenticado.id
        updated_at              : "now"
      }
    } as $regra_criada

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "criar_regra_documento_obrigatorio"
        recurso    : "documento_obrigatorio_regra"
        registro_id: $regra_criada.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Regra de documento obrigatorio cadastrada com sucesso."
    regra   : $regra_criada
  }

  guid = "conectahr-documentos-obrigatorios-post-0001"
}
