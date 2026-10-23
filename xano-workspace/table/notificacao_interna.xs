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
      // pedido_novo: para quem decide; pedido_decidido: o retorno para quem pediu;
      // cadastro_atualizado, documento_pedido e holerite_disponivel: mudancas que afetam a pessoa
      // (parte 2 das notificacoes, 12/10/2026). treinamento_novo e pesquisa_nova: publicacoes para um publico
      // (change notificacoes-de-publicacao).
      values = ["ferias_aprovada", "documento_vencendo", "avaliacao_disponivel", "solicitacao_respondida", "ponto_ajustado", "descanso_interjornada", "beneficio_atualizado", "pedido_novo", "pedido_decidido", "cadastro_atualizado", "documento_pedido", "holerite_disponivel", "treinamento_novo", "pesquisa_nova"]
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
