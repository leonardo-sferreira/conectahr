// Checklist de saida de um desligamento (change fluxo-de-desligamento, D1). Os itens padrao nascem
// na aprovacao; o RH marca cada um; concluir um desligamento agendado exige todos feitos.
table desligamento_checklist {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int solicitacao_desligamento_id {
      table = "solicitacao_desligamento"
    }

    text titulo filters=trim|max:150
    text responsavel filters=trim|max:60
    int ordem?=1
    bool feito?=false
    timestamp? feito_em?
    int? feito_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "solicitacao_desligamento_id", op: "asc"}]}
  ]
  guid = "MbYcknllUCoIFD1sTyidzLwrP-0"
}
