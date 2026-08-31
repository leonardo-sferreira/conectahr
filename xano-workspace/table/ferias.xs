table ferias {
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
  
    timestamp? data_solicitacao
    date? data_inicio
    date? data_fim
    int quantidade_dias
    enum status?=Pendente {
      values = ["Pendente", "Aprovada", "Rejeitada", "Cancelada", "Concluida"]
    }
  
    text observacao_colaborador? filters=trim|max:500
    text observacao_rh? filters=trim|max:500
    int decidido_por_user_id? {
      table = "user"
    }
  
    timestamp? data_decisao?

    // Fonte normativa aplicada na validacao da solicitacao (item 4.4) —
    // qual linha da matriz regra_contrato (e, por ela, qual
    // instrumento_normativo, quando houver) fundamentou os limites
    // checados nesta solicitacao.
    int? regra_contrato_id {
      table = "regra_contrato"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]

  guid = "Rzg-XSqug-ieGUSd29I6UTrnhKc"
}