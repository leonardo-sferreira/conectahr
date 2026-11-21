table solicitacao_desligamento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    int colaborador_id {
      table = "colaborador"
    }
  
    int solicitante_user_id {
      table = "user"
    }
  
    enum origem {
      values = ["funcionario", "gestor"]
    }
  
    enum tipo_desligamento {
      values = ["imediato", "aviso_previo"]
    }
  
    date? data_prevista?
    date? data_efetiva?
    int dias_aviso?
    text motivo_solicitacao filters=trim|max:500
    enum status?=pendente {
      values = [
        "pendente"
        "agendado"
        "em_analise"
        "rejeitada"
        "cancelada"
        "concluido"
      ]
    }
  
    int responsavel_rh_user_id? {
      table = "user"
    }

    timestamp? data_inicio_analise?
    int decidido_por_user_id? {
      table = "user"
    }

    timestamp? data_decisao?
    text? motivo_decisao filters=trim|max:1000
    int cancelado_por_user_id? {
      table = "user"
    }

    timestamp? data_cancelamento?
    text motivo_cancelamento? filters=trim|max:500
    timestamp? data_conclusao?

    // SLA de atendimento gravado na abertura (change sla-de-solicitacoes, D3): o prazo e o ponto de
    // "perto de vencer" (80% das horas uteis) nao mudam se o SLA for alterado depois.
    timestamp? prazo_sla?
    timestamp? alerta_sla?
    int? sla_horas?
    // Quando quem decide foi avisado de que o prazo esta perto de vencer (D7; rotina diaria).
    timestamp? aviso_sla_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
    {
      type : "btree"
      field: [{name: "solicitante_user_id", op: "asc"}]
    }
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {
      type : "btree"
      field: [
        {name: "status", op: "asc"}
        {name: "data_efetiva", op: "asc"}
      ]
    }
  ]

  guid = "53XiVDG-nJ-6bIxKoUJtpH1EGaE"
}