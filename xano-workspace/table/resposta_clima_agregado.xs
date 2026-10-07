// Contagem anonima das respostas da pesquisa de clima: uma linha por
// (pergunta, departamento, nota) com a quantidade de respostas.
// Nao existe registro individual de resposta, entao nao ha id, data ou
// horario que permita cruzar com resposta_clima_participacao.
// Sem created_at/updated_at de proposito.
// departamento_id = 0 significa "sem departamento" (evita nulo no indice unico).
table resposta_clima_agregado {
  auth = false

  schema {
    int id
    int pergunta_clima_id {
      table = "pergunta_clima"
    }
    int departamento_id?=0
    int nota filters=min:1|max:5
    int quantidade?=0
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [
        {name: "pergunta_clima_id", op: "asc"}
        {name: "departamento_id", op: "asc"}
        {name: "nota", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-resposta-clima-agregado-0001"
}
