// Preferencia de aviso por assunto e canal (change configuracoes-seguranca-notificacoes, D2).
// Sem registro, os dois canais estao ligados. Beneficios, alertas de seguranca e pedidos que
// esperam a decisao da pessoa nao tem preferencia: sao sempre entregues.
table preferencia_aviso {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int user_id {
      table = "user"
    }

    enum assunto {
      values = ["ferias_ausencias", "ponto", "documentos", "avaliacoes_metas", "solicitacoes", "treinamentos", "pesquisas"]
    }

    bool plataforma?=true
    bool email?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "user_id", op: "asc"}, {name: "assunto", op: "asc"}]}
  ]
  guid = "k8WZRSEZi-q1kxNSVlPEKXbE9-0"
}
