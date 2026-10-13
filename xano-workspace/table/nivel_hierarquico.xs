// Niveis hierarquicos da empresa (change organograma-hierarquia, D2): cada empresa cadastra os seus
// (ex.: CEO, Diretoria, Head, Gerencia, Coordenacao, Supervisao, Analista, Operador, Estagiario).
// A ordem menor fica em cima no organograma. Mantidos pelo RH e pelo Admin, com auditoria.
table nivel_hierarquico {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    text nome filters=trim|min:2|max:60
    int ordem
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "ordem", op: "asc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]

  guid = "conectahr-nivel-hierarquico-0001"
}
