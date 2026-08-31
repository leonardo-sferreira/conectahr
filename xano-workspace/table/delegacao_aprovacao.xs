table delegacao_aprovacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int titular_user_id {
      table = "user"
    }
    int substituto_user_id {
      table = "user"
    }
    enum escopo {
      values = ["ferias", "ausencia", "documento", "desligamento", "correcao_ponto", "solicitacao_rh", "todas"]
    }
    date data_inicio
    date data_fim
    text motivo filters=trim|min:5|max:1000
    int criado_por_user_id {
      table = "user"
    }
    timestamp? cancelada_em
    int? cancelada_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "titular_user_id", op: "asc"}]}
    {type: "btree", field: [{name: "substituto_user_id", op: "asc"}]}
  ]

  guid = "conectahr-delegacao-aprovacao-0001"
}
