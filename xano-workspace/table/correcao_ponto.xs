table correcao_ponto {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int registro_ponto_id {
      table = "registro_ponto"
    }
    int colaborador_id {
      table = "colaborador"
    }
    enum campo {
      values = ["hora_entrada", "inicio_intervalo", "fim_intervalo", "hora_saida"]
    }
    timestamp? valor_original
    timestamp valor_solicitado
    text justificativa filters=trim|min:5|max:1000
    enum status?=pendente {
      values = ["pendente", "aprovada", "rejeitada"]
    }
    int? decidido_por_user_id {
      table = "user"
    }
    timestamp? data_decisao
    text? motivo_decisao filters=trim|max:1000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "registro_ponto_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-correcao-ponto-0001"
}
