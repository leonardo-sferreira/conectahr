table historico_profissional {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    int colaborador_id {
      table = "colaborador"
    }
  
    int cargo_id {
      table = "cargo"
    }
  
    int departamento_id {
      table = "departamento"
    }
  
    enum nivel? {
      values = ["l1", "l2", "l3", "l4", "l5"]
    }
  
    decimal salario
    enum tipo_contrato {
      values = ["CLT", "PJ", "ESTAGIO", "APRENDIZ", "TEMPORARIO", "OUTRO"]
    }

    decimal carga_horaria_semanal
    date? data_inicio
    date? data_fim?
    enum tipo_alteracao {
      values = [
        "admissao"
        "promocao"
        "alteracao_departamento"
        "alteracao_salarial"
        "alteracao_cargo"
        "alteracao_contratual"
        "desligamento"
      ]
    }
  
    text motivo_alteracao? filters=trim|max:500
    int user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
    {
      type : "btree"
      field: [
        {name: "data_inicio", op: "asc"}
        {name: "colaborador_id", op: "asc"}
      ]
    }
  ]

  guid = "f_BFP8_diXN2hMVjuomw0_0SJgg"
}