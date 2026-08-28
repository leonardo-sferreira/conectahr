table competencia_avaliacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    text nome filters=trim|max:200
    text descricao filters=trim|max:1000
    enum categoria {
      values = ["tecnica", "comportamental", "lideranca", "valor_empresa"]
    }
  
    enum nivel {
      values = ["l1", "l2", "l3", "l4", "l5"]
    }
  
    decimal peso filters=max:100
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [{name: "nivel", op: "asc"}, {name: "ativo", op: "asc"}]
    }
    {type: "btree", field: [{name: "categoria", op: "asc"}]}
  ]

  guid = "N_z2jL_6-urpKwBtyvk8tffnOu0"
}