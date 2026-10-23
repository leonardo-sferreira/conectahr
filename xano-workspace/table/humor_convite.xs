// Convite do termometro de humor por ciclo de 10 dias (change notificacoes-de-publicacao, D3): uma linha
// por ciclo ja convidado, para a rotina diaria nao repetir. Sem pessoa.
table humor_convite {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int ciclo
    int quantidade?=0
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ciclo", op: "asc"}]}
  ]

  guid = "conectahr-humor-convite-0001"
}
