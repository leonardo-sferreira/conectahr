// Quanto cada pessoa assistiu do video de um treinamento (change treinamento-em-video, D2): os segundos
// realmente vistos (trechos pulados nao contam), a posicao onde parou e quando foi a ultima atualizacao (usada
// para recusar progresso mais rapido que o tempo real em 2x). Uma linha por pessoa e treinamento; zera ao concluir.
table treinamento_progresso {
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

    int segundos_vistos?=0
    int posicao?=0
    timestamp? atualizado_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "treinamento_id", op: "asc"}, {name: "colaborador_id", op: "asc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-treinamento-progresso-0001"
}
