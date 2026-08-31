table historico_gestor_departamento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int departamento_id {
      table = "departamento"
    }
    int colaborador_id {
      table = "colaborador"
    }
    timestamp data_inicio
    timestamp? data_fim
    int definido_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "departamento_id", op: "asc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-historico-gestor-departamento-0001"
}
