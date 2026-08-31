table sessao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int user_id {
      table = "user"
    }
    timestamp expira_em
    timestamp? revogada_em?
    text? dispositivo filters=trim|max:255
    text? endereco_ip filters=trim|max:64
    bool ativa?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "user_id", op: "asc"}]}
    {
      type : "btree"
      field: [
        {name: "user_id", op: "asc"}
        {name: "ativa", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-sessao-0001"
}
