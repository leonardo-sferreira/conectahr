// Preferencia de canal/frequencia de notificacao por evento nao-critico
// (item 7.8). Alertas obrigatorios de seguranca (codigo de acesso de
// login, redefinicao de senha, alerta de acesso suspeito) NUNCA passam
// por esta tabela — nao existem como valor do enum tipo_evento, entao
// nao ha como desativa-los por design, nao so por checagem em runtime.
table preferencia_notificacao {
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
    enum tipo_evento {
      values = ["documento_vencendo", "solicitacao_respondida", "avaliacao_disponivel", "ferias_aprovada", "documento_pendente"]
    }
    bool canal_email?=true
    enum frequencia?=imediato {
      values = ["imediato", "resumo_diario", "resumo_semanal"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [
        {name: "user_id", op: "asc"}
        {name: "tipo_evento", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-preferencia-notificacao-0001"
}
