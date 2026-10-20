// Contagem anonima das respostas da pesquisa de clima: uma linha por
// (pergunta, departamento, nota) com a quantidade de respostas.
// Nao existe registro individual de resposta, entao nao ha id, data ou
// horario que permita cruzar com resposta_clima_participacao.
// Sem created_at/updated_at de proposito.
// A nota vai de 1 a 5 (concordancia) ou de 0 a 10 (nps), conforme a escala da pergunta.
// departamento_id = 0 significa "sem departamento" (evita nulo no indice unico).
table resposta_clima_agregado {
  auth = false

  schema {
    int id
    int pergunta_clima_id {
      table = "pergunta_clima"
    }
    int departamento_id?=0
    int nota filters=min:0|max:10
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
