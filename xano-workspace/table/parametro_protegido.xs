table parametro_protegido {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    enum parametro {
      values = ["horas_diarias", "horas_semanais", "intervalo_minutos", "permite_hora_extra", "limite_hora_extra_diaria", "permite_banco_horas", "prazo_compensacao_banco_horas", "controle_ponto", "dias_ferias", "permite_fracionamento", "maximo_periodos", "minimo_periodo_principal", "minimo_outros_periodos", "antecedencia_ferias", "permite_solicitacao_ferias"]
    }
    enum nivel_protecao {
      values = ["configuravel", "configuravel_com_aprovacao", "sem_override"]
    }
    text? descricao filters=trim|max:500
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "parametro", op: "asc"}]}
  ]

  guid = "conectahr-parametro-protegido-0001"
}
