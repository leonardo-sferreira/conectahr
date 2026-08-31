table onboarding_item {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int onboarding_id {
      table = "onboarding"
    }
    enum categoria {
      values = [
        "dados_pessoais"
        "acesso"
        "troca_senha"
        "documentos_obrigatorios"
        "aprovacoes"
        "gestor"
        "departamento"
        "contrato"
        "jornada"
        "metas_iniciais"
        "acompanhamento_30_dias"
        "acompanhamento_60_dias"
        "acompanhamento_90_dias"
      ]
    }
    text descricao filters=trim|max:300
    enum responsavel {
      values = ["rh", "colaborador", "gestor"]
    }
    bool concluido?=false
    int? concluido_por_user_id {
      table = "user"
    }
    timestamp? concluido_em
    text? evidencia filters=trim|max:500
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "onboarding_id", op: "asc"}]}
  ]

  guid = "conectahr-onboarding-item-0001"
}
