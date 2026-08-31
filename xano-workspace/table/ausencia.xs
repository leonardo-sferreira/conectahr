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
    text motivo? filters=trim
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