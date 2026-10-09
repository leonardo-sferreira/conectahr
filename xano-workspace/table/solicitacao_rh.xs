table solicitacao_rh {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int colaborador_id {
      table = "colaborador"
    }
    enum tipo {
      values = ["alteracao_cadastral", "declaracao", "documento_avulso", "outra", "privacidade_lgpd"]
    }

    // Pedido do titular de dados (LGPD, arts. 18 e 19): so quando tipo = privacidade_lgpd.
    // Os sete subtipos: confirmacao_acesso (art. 18, I e II), correcao (III),
    // anonimizacao_eliminacao (IV e VI), portabilidade (V), informacao_compartilhamento
    // (VII), revogacao_consentimento (IX) e oposicao (art. 18, par. 2).
    enum? subtipo_lgpd {
      values = ["confirmacao_acesso", "correcao", "anonimizacao_eliminacao", "portabilidade", "informacao_compartilhamento", "revogacao_consentimento", "oposicao"]
    }

    // Prazo para responder o pedido LGPD: abertura + 15 dias (art. 19, II).
    date? prazo_resposta?
    text descricao filters=trim|min:5|max:2000
    enum status?=recebida {
      values = ["recebida", "em_analise", "atendida", "indeferida"]
    }
    int? decidido_por_user_id {
      table = "user"
    }
    text? justificativa_decisao filters=trim|max:1000
    timestamp? data_decisao
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-solicitacao-rh-0001"
}
