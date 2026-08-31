table pesquisa_clima {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    text titulo filters=trim|max:200
    text? descricao filters=trim|max:1000
    date data_inicio
    date data_fim
    int minimo_respostas?=5
    int criado_por_user_id {
      table = "user"
    }
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]

  guid = "conectahr-pesquisa-clima-0001"
}
