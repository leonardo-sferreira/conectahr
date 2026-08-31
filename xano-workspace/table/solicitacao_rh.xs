table solicitacao_rh {
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
    enum tipo {
      values = ["alteracao_cadastral", "declaracao", "documento_avulso", "outra"]
    }
    text descricao filters=trim|min:5|max:2000
    enum status?=recebida {
      values = ["recebida", "em_analise", "atendida", "indeferida"]
    }
    int? decidido_por_user_id {
      table = "user"
    }
    text? justificativa_decisao filters=trim|max:1000
    timestamp? data_decisao
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-solicitacao-rh-0001"
}
