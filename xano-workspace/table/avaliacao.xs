table avaliacao {
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

    int user_id {
      table = "user"
    }

    int? ciclo_avaliacao_id {
      table = "ciclo_avaliacao"
    }

    enum relacao_avaliador {
      values = ["autoavaliacao", "gestor", "par", "subordinado", "rh"]
    }

    date? periodo_incio
    date? periodo_fim
    decimal nota? filters=max:10
    text comentario? filters=trim|max:2000
    timestamp? data_avaliacao?
    enum status?=pendente {
      values = ["pendente", "em_andamento", "enviada", "cancelada"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "user_id", op: "asc"}
      ]
    }
    {
      type : "btree"
      field: [{name: "user_id", op: "asc"}, {name: "status", op: "asc"}]
    }
    {
      type : "btree"
      field: [
        {name: "ciclo_avaliacao_id", op: "asc"}
        {name: "colaborador_id", op: "asc"}
      ]
    }
  ]

  guid = "X-PQ1xB3-dF2t6NLv6eqY9-VYt8"
}