table ciclo_avaliacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    text nome filters=trim|max:100
    text descricao filters=trim|max:500
    date? data_inicio
    date? data_checkin
    date? data_fim
    enum status?=planejamento {
      values = [
        "planejamento"
        "em_andamento"
        "fechamento"
        "concluido"
        "cancelado"
      ]
    }
  
    int criado_por_user_id {
      table = "user"
    }
  
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
    {
      type : "btree"
      field: [
        {name: "data_inicio", op: "asc"}
        {name: "data_fim", op: "asc"}
      ]
    }
  ]

  guid = "qDS9EdcQrl-xpNCuDkMV3ICkddg"
}