table pendencia_documento {
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
    enum tipo_documento {
      values = [
        "rg"
        "cpf"
        "cin"
        "cnh"
        "ctps"
        "aso_admissional"
        "laudo_deficiencia"
        "certificado_profissional"
        "comprovante_residencia"
        "comprovante_escolaridade"
        "registro_profissional"
        "documentacao_migratoria"
        "certificado_reservista"
        "documentacao_responsavel_legal"
        "outro"
      ]
    }
    date prazo
    text? observacao filters=trim|max:500
    enum status?=pendente {
      values = ["pendente", "atendida", "cancelada"]
    }
    int solicitado_por_user_id {
      table = "user"
    }
    int? atendida_por_documento_id {
      table = "documento"
    }
    timestamp? atendida_em
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-pendencia-documento-0001"
}
