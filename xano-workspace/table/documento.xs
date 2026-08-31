table documento {
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
        "holerite"
        "informe_rendimentos"
      ]
    }

    text nome_documento filters=trim|max:120
    text numero_documento? filters=trim|max:50
    text? estado_de_emissao filters=trim
    date? data_emissao?
    date? data_validade?
    text observacao? filters=trim|max:500
    enum status?=pendente_analise {
      values = ["pendente_analise", "aprovado", "rejeitado", "vencido", "substituido", "arquivado"]
    }
    enum estado_verificacao?=enviado {
      values = ["enviado", "em_verificacao", "liberado", "bloqueado"]
    }
    int? ultimo_alerta_dias
    text? hash_arquivo filters=trim|max:128
    int? documento_substituido_id {
      table = "documento"
    }
    text? motivo_bloqueio filters=trim|max:500
    image? imagem_frente
    image? imagem_verso
    text arquivo_url? filters=trim
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "Oj-w_vYdAkS_X8HfERafqXqx0jU"
}