table meta_avaliacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    int ciclo_avaliacao_id {
      table = "ciclo_avaliacao"
    }
  
    int colaborador_id {
      table = "colaborador"
    }
  
    text titulo filters=trim|max:500
    text descricao filters=trim|max:500
    text indicador filters=trim|max:300
    decimal valor_esperado?
    text unidade_medida? filters=trim|max:50
    decimal peso filters=max:100
    date? data_prazo
    decimal progresso_percentual? filters=max:100
    text comentario_checkin? filters=trim|max:2000
    timestamp? data_checkin_realizado?
    decimal resultado_final? filters=max:100
    text comentario_final? filters=trim|max:2000
    enum status?=planejada {
      values = ["planejada", "em_andamento", "concluida", "cancelada"]
    }
  
    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "ciclo_avaliacao_id", op: "asc"}
        {name: "colaborador_id", op: "asc"}
      ]
    }
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "5PWf3VHh9l_0jl_AikcrBpgd95Y"
}