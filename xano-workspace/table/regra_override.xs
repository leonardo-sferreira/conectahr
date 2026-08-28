table regra_override {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int instrumento_normativo_id {
      table = "instrumento_normativo"
    }
    enum parametro {
      values = ["horas_diarias", "horas_semanais", "intervalo_minutos", "permite_hora_extra", "limite_hora_extra_diaria", "permite_banco_horas", "prazo_compensacao_banco_horas", "controle_ponto", "dias_ferias", "permite_fracionamento", "maximo_periodos", "minimo_periodo_principal", "minimo_outros_periodos", "antecedencia_ferias", "permite_solicitacao_ferias"]
    }
    text valor_anterior? filters=trim|max:500
    text valor_novo filters=trim|max:500
    int prioridade
    enum abrangencia {
      values = ["empresa", "estabelecimento", "estado", "municipio", "departamento", "cargo", "tipo_contrato", "categoria_profissional", "colaborador"]
    }
    int? departamento_id {
      table = "departamento"
    }
    int? cargo_id {
      table = "cargo"
    }
    int? colaborador_id {
      table = "colaborador"
    }
    text? tipo_contrato filters=trim|max:20
    text? estado filters=trim|max:100
    text? municipio filters=trim|max:120
    text? categoria_profissional filters=trim|max:200
    date data_inicio
    date? data_fim
    enum tipo_aplicacao?=futura {
      values = ["futura", "retroativa"]
    }
    text? justificativa filters=trim|max:2000
    int versao?=1
    bool ativo?=false
    enum status?=rascunho {
      values = ["rascunho", "pendente_aprovacao", "aprovada", "vigente", "encerrada", "suspensa", "revogada", "rejeitada"]
    }
    int criado_por_user_id {
      table = "user"
    }
    int? aprovado_por_user_id {
      table = "user"
    }
    timestamp? data_aprovacao
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "instrumento_normativo_id", op: "asc"}]}
    {type: "btree", field: [{name: "abrangencia", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {type: "btree", field: [{name: "data_inicio", op: "desc"}]}
  ]
}
