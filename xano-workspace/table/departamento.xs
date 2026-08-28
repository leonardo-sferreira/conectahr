table departamento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    text nome filters=trim|min:2|max:80
    text descricao? filters=trim
    bool ativo?=true
    int gestor_colaborador_id? {
      table = "colaborador"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]

  guid = "NDABUGiP_H-v2VVXfWZYKOvDuEE"
}