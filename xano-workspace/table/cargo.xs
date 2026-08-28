table cargo {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    text nome filters=trim|max:100|min:2
    text descricao? filters=trim
    decimal salario_base?
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]

  guid = "5gK8xV8e14N8eSU0GzGCFv07FYg"
}