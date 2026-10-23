// Termometro de humor (change termometro-de-humor, D2): quem ja respondeu qual ciclo, so para bloquear a
// segunda resposta. Sem nota, motivo nem data: nunca e cruzada com as contagens.
table humor_participacao {
  auth = false

  schema {
    int id
    int ciclo
    int colaborador_id {
      table = "colaborador"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ciclo", op: "asc"}, {name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-humor-participacao-0001"
}
