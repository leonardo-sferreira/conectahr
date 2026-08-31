table registro_ponto {
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
  
    date? data
    timestamp? hora_entrada?
    timestamp? inicio_intervalo?
    timestamp? fim_intervalo?
    timestamp? hora_saida?
    decimal horas_trabalhadas?
    decimal horas_extras?
    enum status {
      values = ["Aberto", "Completo", "Incompleto", "Ajustado"]
    }

    text observacao? filters=trim|max:500
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree|unique"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "data", op: "asc"}
      ]
    }
  ]

  guid = "Zsw7bwIJvGp6krUQN1TOXTFFd0Y"
}