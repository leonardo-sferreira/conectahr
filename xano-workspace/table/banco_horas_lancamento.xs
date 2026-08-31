// Ledger append-only: nunca ha edicao nem exclusao de lancamento, so
// criacao. O saldo e sempre a soma (credito - debito), nunca um campo
// gravado a parte - por isso "o saldo nao pode ser apagado
// manualmente" (item 4.14): nao existe operacao que apague ou
// sobrescreva um lancamento ja registrado.
table banco_horas_lancamento {
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
      values = ["credito", "debito"]
    }
    decimal horas filters=min:0.01
    text origem filters=trim|max:200
    int? instrumento_normativo_id {
      table = "instrumento_normativo"
    }
    date data_lancamento
    date? data_expiracao
    int registrado_por_user_id {
      table = "user"
    }
    text? observacao filters=trim|max:500
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-banco-horas-lancamento-0001"
}
