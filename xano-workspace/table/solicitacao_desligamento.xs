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