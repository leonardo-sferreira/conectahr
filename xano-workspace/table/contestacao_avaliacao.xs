table contestacao_avaliacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int avaliacao_id {
      table = "avaliacao"
    }
    int colaborador_id {
      table = "colaborador"
    }
    text motivo filters=trim|min:5|max:2000
    enum status?=aberta {
      values = ["aberta", "revisada"]
    }
    int? revisado_por_user_id {
      table = "user"
    }
    text? resposta_revisao filters=trim|max:2000
    timestamp? data_revisao
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "avaliacao_id", op: "asc"}]}
  ]

  guid = "conectahr-contestacao-avaliacao-0001"
}
