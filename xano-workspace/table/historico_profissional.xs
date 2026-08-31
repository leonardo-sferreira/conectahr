table historico_profissional {
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

    // Estado das integracoes eSocial e CTPS Digital — so relevante para
    // tipo_alteracao=="admissao" com tipo_contrato=="CLT" (item 3.5).
    // Sao integracoes futuras (design.md): o MVP rastreia manualmente o
    // estado que o RH confirma, sem chamar servico externo, sem mascarar
    // indisponibilidade.
    enum? esocial_status?=pendente {
      values = ["pendente", "comunicado", "confirmado", "indisponivel"]
    }

    date? esocial_prazo
    enum? ctps_status?=pendente {
      values = ["pendente", "comunicado", "confirmado", "indisponivel"]
    }

    date? ctps_prazo
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