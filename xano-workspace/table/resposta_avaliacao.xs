table resposta_avaliacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    int avaliacao_id {
      table = "avaliacao"
    }
  
    int competencia_avaliacao_id {
      table = "competencia_avaliacao"
    }
  
    int nota filters=min:1|max:5
    text comentario? filters=trim|max:2000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree|unique"
      field: [
        {name: "avaliacao_id", op: "asc"}
        {name: "competencia_avaliacao_id", op: "asc"}
      ]
    }
  ]

  guid = "BNDpCs2Oibl3yxqqPAmpaCyO_eA"
}