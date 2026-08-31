// Central de notificacoes internas (item 5.11): criada junto com todo
// evento que tambem dispara um e-mail assincrono (ver email_outbox),
// para o usuario poder ver dentro do proprio ConectaRH sem depender do
// e-mail chegar.
table notificacao_interna {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int destinatario_user_id {
      table = "user"
    }

    enum tipo {
      values = ["ferias_aprovada", "documento_vencendo", "avaliacao_disponivel", "solicitacao_respondida"]
    }

    text titulo filters=trim|max:150
    text mensagem filters=trim|max:1000
    text recurso filters=trim|max:50
    int? registro_id
    bool lida?=false
    timestamp? lida_em
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "destinatario_user_id", op: "asc"}
        {name: "lida", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-notificacao-interna-0001"
}
