table onboarding {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int colaborador_id {
      table = "colaborador"
    }
    int iniciado_por_user_id {
      table = "user"
    }
    date data_inicio
    enum status?=em_andamento {
      values = ["em_andamento", "concluido"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-onboarding-0001"
}
