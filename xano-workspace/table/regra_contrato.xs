table regra_contrato {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    enum tipo_contrato {
      values = ["CLT", "PJ", "ESTAGIO", "APRENDIZ", "TEMPORARIO", "OUTRO"]
    }
    decimal? horas_diarias
    decimal? horas_semanais
    int? intervalo_minutos
    bool? permite_hora_extra
    decimal? limite_hora_extra_diaria
    bool? permite_banco_horas
    int? prazo_compensacao_banco_horas
    enum controle_ponto? {
      values = ["obrigatorio", "nao_aplicavel", "manual"]
    }
    int? periodo_aquisitivo_meses
    int? dias_ferias_recesso
    bool? proporcional
    bool? permite_fracionamento
    int? maximo_periodos
    int? minimo_periodo_principal
    int? minimo_outros_periodos
    int? antecedencia_ferias
    bool? permite_solicitacao_ferias
    date data_inicio
    date? data_fim
    bool ativo?=true
    int? instrumento_normativo_id {
      table = "instrumento_normativo"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "tipo_contrato", op: "asc"}]}
    {type: "btree", field: [{name: "data_inicio", op: "desc"}]}
    {type: "btree", field: [{name: "data_fim", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]
  guid = "JNcQIBppdEmMxFSmfmVhPMJ0Ocw"
}
