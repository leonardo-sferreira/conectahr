table registro_ponto {
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
  
    date? data
    timestamp? hora_entrada?
    timestamp? inicio_intervalo?
    timestamp? fim_intervalo?
    timestamp? hora_saida?
    decimal horas_trabalhadas?
    decimal horas_extras?
    enum status {
      values = ["Aberto", "Completo", "Incompleto", "Ajustado"]
    }

    text observacao? filters=trim|max:500
    // Jornada (change ponto-rep-p-e-ferias-clt, D13 e D14): saldo do dia contra a jornada do
    // contrato, com a tolerancia diaria; descanso desde a ultima marcacao valida do dia anterior.
    int? saldo_minutos
    int? descanso_minutos
    timestamp? primeira_valida
    timestamp? ultima_valida
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree|unique"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "data", op: "asc"}
      ]
    }
  ]

  guid = "Zsw7bwIJvGp6krUQN1TOXTFFd0Y"
}