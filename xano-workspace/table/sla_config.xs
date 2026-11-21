// SLA de atendimento por setor responsavel e tipo de solicitacao, em horas uteis (change
// sla-de-solicitacoes, D1). Sem linha ativa, vale o padrao de 72 horas uteis. So o Admin grava.
table sla_config {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    enum setor {
      values = ["rh", "gestor", "admin"]
    }
    enum tipo_solicitacao {
      values = ["alteracao_cadastral", "declaracao", "documento_avulso", "outra", "privacidade_lgpd", "desligamento", "ferias", "ausencia", "correcao_ponto", "acesso"]
    }
    int horas_uteis
    bool ativo?=true
    int? atualizado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [
        {name: "setor", op: "asc"}
        {name: "tipo_solicitacao", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-sla-config-0001"
}
