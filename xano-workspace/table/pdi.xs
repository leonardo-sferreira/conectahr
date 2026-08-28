table pdi {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    int ciclo_avaliacao_id {
      table = "ciclo_avaliacao"
    }
  
    int colaborador_id {
      table = "colaborador"
    }
  
    text titulo filters=trim|max:150
    text descricao filters=trim|max:2000
    text acao_desenvolvimento filters=trim|max:2000
    int responsavel_user_id {
      table = "user"
    }
  
    date? data_inicio
    date? data_prazo
    decimal progresso_percentual? filters=max:100|min:0
    enum status?=planejado {
      values = ["planejado", "em_andamento", "concluido", "cancelado"]
    }
  
    text evidencia? filters=trim|max:2000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
    {
      type : "btree"
      field: [
        {name: "ciclo_avaliacao_id", op: "asc"}
        {name: "colaborador_id", op: "asc"}
      ]
    }
  ]

  guid = "VFlApw0fRRSv0xy-QNOlCdwbOlY"
}