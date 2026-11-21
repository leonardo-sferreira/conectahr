// Pedido do RH para o Admin trocar o perfil de acesso de uma conta (change pedido-de-acesso).
// O RH escolhe o perfil e justifica; o Admin aprova (o perfil e trocado na hora) ou recusa com motivo.
table solicitacao_acesso {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int usuario_id {
      table = "user"
    }

    int colaborador_id? {
      table = "colaborador"
    }

    int solicitante_user_id {
      table = "user"
    }

    enum perfil_atual {
      values = ["Admin", "RH", "Gestor", "Colaborador"]
    }

    enum perfil_solicitado {
      values = ["Admin", "RH", "Gestor", "Colaborador"]
    }

    text justificativa filters=trim|max:1000
    enum status?=pendente {
      values = ["pendente", "aprovada", "recusada"]
    }

    int decidido_por_user_id? {
      table = "user"
    }

    timestamp? data_decisao?
    text? motivo_decisao filters=trim|max:1000

    // SLA de atendimento gravado na abertura (change sla-de-solicitacoes, D3): o prazo e o ponto de
    // "perto de vencer" (80% das horas uteis) nao mudam se o SLA for alterado depois.
    timestamp? prazo_sla?
    timestamp? alerta_sla?
    int? sla_horas?
    // Quando quem decide foi avisado de que o prazo esta perto de vencer (D7; rotina diaria).
    timestamp? aviso_sla_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "usuario_id", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]
  guid = "8_hCzSwO0ZW7NxTg90DMHAJT9-0"
}
