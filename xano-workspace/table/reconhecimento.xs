table reconhecimento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    int remetente_user_id {
      table = "user"
    }
  
    int destinatario_colaborador_id {
      table = "colaborador"
    }
  
    int competencia_avaliacao_id {
      table = "competencia_avaliacao"
    }
  
    text titulo filters=trim|max:100
    text mensagem filters=trim|max:1500
    enum visibilidade?=publico {
      values = ["publico", "privado"]
    }
  
    enum status?=ativo {
      values = ["ativo", "cancelado", "moderado"]
    }
  
    int moderado_por_user_id? {
      table = "user"
    }
  
    text motivo_moderacao? filters=trim|max:1000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "destinatario_colaborador_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
    {
      type : "btree"
      field: [
        {name: "remetente_user_id", op: "asc"}
        {name: "created_at", op: "asc"}
      ]
    }
  ]

  guid = "ZLa_v3MhNANv2NdGMCBBldrvRW8"
}