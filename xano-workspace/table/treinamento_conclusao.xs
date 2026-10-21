// Conclusao de um treinamento por uma pessoa (change treinamentos-obrigatorios, D1): a data, a validade
// calculada (concluido_em + validade_meses; sem validade, nula), o instrutor e o link do certificado.
// O RH registra; so inclusao (corrigir = registrar de novo).
table treinamento_conclusao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int treinamento_id {
      table = "treinamento"
    }

    int colaborador_id {
      table = "colaborador"
    }

    date concluido_em
    date? valido_ate
    text? instrutor filters=trim|max:150
    text? certificado_url filters=trim|max:500
    int registrado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "treinamento_id", op: "asc"}, {name: "colaborador_id", op: "asc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-treinamento-conclusao-0001"
}
