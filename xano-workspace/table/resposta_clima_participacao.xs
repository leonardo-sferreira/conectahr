// Controla quem ja respondeu qual pergunta, so para bloquear resposta
// duplicada - nunca e cruzada com `resposta_clima` (que nao tem
// identidade nenhuma), entao nao compromete o anonimato da nota em si.
table resposta_clima_participacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int pergunta_clima_id {
      table = "pergunta_clima"
    }
    int colaborador_id {
      table = "colaborador"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [
        {name: "pergunta_clima_id", op: "asc"}
        {name: "colaborador_id", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-resposta-clima-participacao-0001"
}
