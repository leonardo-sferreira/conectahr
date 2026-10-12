table feriado {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    date data
    text nome filters=trim|max:200
    enum abrangencia?=nacional {
      values = ["nacional", "estadual", "municipal"]
    }
    // Feriado ou ponto facultativo (change ponto-rep-p-e-ferias-clt).
    enum tipo?=feriado {
      values = ["feriado", "ponto_facultativo"]
    }
    // Ex.: "apos as 14h", "ate as 14h".
    text? observacao filters=trim|max:100
    text? estado filters=trim|max:100
    text? municipio filters=trim|max:120
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "data", op: "asc"}]}
  ]

  guid = "conectahr-feriado-0001"
}
