table ausencia {
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
      values = ["Falta", "Atestado", "Afastamento", "Licenca", "Outro"]
    }

    date? data_inicio
    date? data_fim
    // Texto livre LEGADO: pode conter diagnostico. Fica privado (fora das respostas)
    // e sem novas gravacoes (LGPD); o motivo agora e escolhido em motivo_tipo.
    text motivo? filters=trim {
      visibility = "private"
    }
    enum? motivo_tipo {
      values = ["consulta", "doenca", "acompanhamento_familiar", "outro"]
    }
    image? comprovante?
    enum status {
      values = ["Pendente", "Aprovada", "Rejeitada", "Registrado"]
    }

    text observacao? filters=trim|max:500

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
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "JxTOSwc09acLMDtxIE2EUrFWPCs"
}