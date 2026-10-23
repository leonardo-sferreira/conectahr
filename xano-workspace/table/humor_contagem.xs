// Termometro de humor (change termometro-de-humor, D2): contagem anonima das notas, uma linha por
// (ciclo de 10 dias, departamento, nota) com a quantidade. Nao existe registro individual: sem pessoa, data
// ou horario, entao nao ha como cruzar com humor_participacao. Sem created_at de proposito.
// Nota de 1 (muito mal) a 5 (muito bem). departamento_id = 0: sem departamento (evita nulo no indice unico).
table humor_contagem {
  auth = false

  schema {
    int id
    int ciclo
    int departamento_id?=0
    int nota filters=min:1|max:5
    int quantidade?=0
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ciclo", op: "asc"}, {name: "departamento_id", op: "asc"}, {name: "nota", op: "asc"}]}
  ]

  guid = "conectahr-humor-contagem-0001"
}
