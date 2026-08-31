// Catalogo com os valores validos de todos os enums do dominio
// ConectaRH (para popular selects/dropdowns no frontend e servir de
// referencia unica). Os valores sao os mesmos ja impostos pelo tipo
// `enum` de cada tabela e pela validacao explicita de cada endpoint de
// escrita — este catalogo nao substitui essa validacao, apenas a
// expõe de forma consultavel. Aberto a qualquer usuario autenticado.
query catalogos verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_usuario {
      value = ["Admin", "RH", "Colaborador", "Gestor"]
    }

    var $tipo_contrato {
      value = ["CLT", "PJ", "ESTAGIO", "APRENDIZ", "TEMPORARIO", "OUTRO"]
    }

    var $nivel_colaborador {
      value = ["l1", "l2", "l3", "l4", "l5"]
    }

    var $status_colaborador {
      value = ["Ativo", "Ferias", "Afastado", "Desligado"]
    }

    var $tipo_conta_bancaria {
      value = ["corrente", "poupanca"]
    }

    var $tipo_ausencia {
      value = ["Falta", "Atestado", "Afastamento", "Licenca", "Outro"]
    }

    var $status_ausencia {
      value = ["Pendente", "Aprovada", "Rejeitada", "Registrado"]
    }

    var $status_ferias {
      value = ["Pendente", "Aprovada", "Rejeitada", "Cancelada", "Concluida"]
    }

    var $tipo_documento {
      value = ["rg", "cpf", "cin", "cnh", "ctps", "aso_admissional", "laudo_deficiencia", "certificado_profissional", "comprovante_residencia", "comprovante_escolaridade", "registro_profissional", "documentacao_migratoria", "certificado_reservista", "documentacao_responsavel_legal", "outro"]
    }

    var $status_documento {
      value = ["pendente_analise", "aprovado", "rejeitado", "vencido", "substituido", "arquivado"]
    }

    var $estado_verificacao_documento {
      value = ["enviado", "em_verificacao", "liberado", "bloqueado"]
    }

    var $origem_desligamento {
      value = ["funcionario", "gestor"]
    }

    var $tipo_desligamento {
      value = ["imediato", "aviso_previo"]
    }

    var $status_desligamento {
      value = ["pendente", "agendado", "em_analise", "rejeitada", "cancelada", "concluido"]
    }

    var $status_ponto {
      value = ["Aberto", "Completo", "Incompleto", "Ajustado"]
    }

    var $controle_ponto_contrato {
      value = ["obrigatorio", "nao_aplicavel", "manual"]
    }

    var $tipo_alteracao_historico {
      value = ["admissao", "promocao", "alteracao_departamento", "alteracao_salarial", "alteracao_cargo", "alteracao_contratual", "desligamento"]
    }

    var $visibilidade_reconhecimento {
      value = ["publico", "privado"]
    }

    var $status_reconhecimento {
      value = ["ativo", "cancelado", "moderado"]
    }

    var $tipo_instrumento_normativo {
      value = ["acordo_coletivo", "convencao_coletiva", "termo_aditivo", "regime_especial", "norma_legal", "decisao_judicial", "acordo_individual_autorizado"]
    }

    var $status_instrumento_normativo {
      value = ["rascunho", "pendente_aprovacao", "vigente", "suspenso", "expirado", "revogado", "rejeitado"]
    }

    var $parametro_regra_override {
      value = ["horas_diarias", "horas_semanais", "intervalo_minutos", "permite_hora_extra", "limite_hora_extra_diaria", "permite_banco_horas", "prazo_compensacao_banco_horas", "controle_ponto", "dias_ferias", "permite_fracionamento", "maximo_periodos", "minimo_periodo_principal", "minimo_outros_periodos", "antecedencia_ferias", "permite_solicitacao_ferias"]
    }

    var $abrangencia_regra_override {
      value = ["empresa", "estabelecimento", "estado", "municipio", "departamento", "cargo", "tipo_contrato", "categoria_profissional", "colaborador"]
    }

    var $tipo_aplicacao_regra_override {
      value = ["futura", "retroativa"]
    }

    var $status_regra_override {
      value = ["rascunho", "pendente_aprovacao", "aprovada", "vigente", "encerrada", "suspensa", "revogada", "rejeitada"]
    }

    var $solicitacao_rh_tipo {
      value = ["alteracao_cadastral", "declaracao", "documento_avulso", "outra"]
    }

    var $solicitacao_rh_status {
      value = ["recebida", "em_analise", "atendida", "indeferida"]
    }
  }

  response = {
    sucesso                      : true
    perfil_usuario                : $perfil_usuario
    tipo_contrato                 : $tipo_contrato
    nivel_colaborador             : $nivel_colaborador
    status_colaborador            : $status_colaborador
    tipo_conta_bancaria           : $tipo_conta_bancaria
    tipo_ausencia                 : $tipo_ausencia
    status_ausencia                : $status_ausencia
    status_ferias                  : $status_ferias
    tipo_documento                  : $tipo_documento
    status_documento                : $status_documento
    estado_verificacao_documento    : $estado_verificacao_documento
    origem_desligamento             : $origem_desligamento
    tipo_desligamento               : $tipo_desligamento
    status_desligamento             : $status_desligamento
    status_ponto                    : $status_ponto
    controle_ponto_contrato         : $controle_ponto_contrato
    tipo_alteracao_historico        : $tipo_alteracao_historico
    visibilidade_reconhecimento     : $visibilidade_reconhecimento
    status_reconhecimento           : $status_reconhecimento
    tipo_instrumento_normativo      : $tipo_instrumento_normativo
    status_instrumento_normativo    : $status_instrumento_normativo
    parametro_regra_override        : $parametro_regra_override
    abrangencia_regra_override      : $abrangencia_regra_override
    tipo_aplicacao_regra_override   : $tipo_aplicacao_regra_override
    status_regra_override           : $status_regra_override
    solicitacao_rh_tipo             : $solicitacao_rh_tipo
    solicitacao_rh_status           : $solicitacao_rh_status
  }

  guid = "conectahr-catalogos-get-0001"
}
