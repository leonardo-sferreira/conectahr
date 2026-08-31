table pergunta_clima {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int pesquisa_clima_id {
      table = "pesquisa_clima"
    }
    text texto filters=trim|max:500
    int ordem?=1
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "pesquisa_clima_id", op: "asc"}]}
  ]

  guid = "conectahr-pergunta-clima-0001"
}
