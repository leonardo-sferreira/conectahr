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
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "JxTOSwc09acLMDtxIE2EUrFWPCs"
}