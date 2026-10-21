table pergunta_clima {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    int pesquisa_clima_id {
      table = "pesquisa_clima"
    }
    text texto filters=trim|max:500
    int ordem?=1

    // Escala da resposta (change pesquisa-clima-e-avaliacao-360, D1): concordancia = 1 a 5
    // (discordo totalmente a concordo totalmente); nps = 0 a 10 (recomendaria a empresa).
    enum escala?=concordancia {
      values = ["concordancia", "nps", "frequencia"]
    }

    // Avaliacao psicossocial (change riscos-psicossociais, D1): a dimensao da NR-1 e o sentido
    // da pergunta. risco = quanto mais frequente, maior o risco; protecao = o contrario.
    // frequencia = 1 a 5 (nunca, raramente, as vezes, frequentemente, sempre).
    text? dimensao filters=trim|max:60
    enum? sentido {
      values = ["risco", "protecao"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "pesquisa_clima_id", op: "asc"}]}
  ]

  guid = "conectahr-pergunta-clima-0001"
}
