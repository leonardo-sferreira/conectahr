// Comentario opcional da pesquisa de clima (change pesquisa-clima-e-avaliacao-360, D1).
// Anonimo como as notas: sem colaborador, sem departamento e sem data ou horario,
// entao nao ha como cruzar com resposta_clima_participacao. O RH so le os textos
// depois do encerramento, em ordem alfabetica (nao na ordem de gravacao) e sem o id,
// e so quando a pesquisa atinge o minimo de respostas.
table comentario_clima {
  auth = false

  schema {
    int id
    int pesquisa_clima_id {
      table = "pesquisa_clima"
    }

    text texto filters=trim|max:1000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "pesquisa_clima_id", op: "asc"}]}
  ]

  guid = "conectahr-comentario-clima-0001"
}
