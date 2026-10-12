table correcao_ponto {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?
    int registro_ponto_id {
      table = "registro_ponto"
    }
    int colaborador_id {
      table = "colaborador"
    }
    // REP-P (change ponto-rep-p-e-ferias-clt): "inclusao" pede uma marcacao que faltou
    // (valor_solicitado = data e hora pedida); "desconsideracao" pede para desconsiderar
    // a marcacao marcacao_id; "alteracao" corrige o horario da marcacao marcacao_id para
    // valor_solicitado (aprovada, vira desconsideracao da original + inclusao do horario certo).
    // "ajuste_campo" e o formato antigo, por campo do dia.
    enum tipo?=ajuste_campo {
      values = ["ajuste_campo", "inclusao", "desconsideracao", "alteracao"]
    }
    int? marcacao_id {
      table = "marcacao_ponto"
    }
    enum? campo? {
      values = ["hora_entrada", "inicio_intervalo", "fim_intervalo", "hora_saida"]
    }
    timestamp? valor_original
    timestamp? valor_solicitado
    text justificativa filters=trim|min:5|max:1000
    enum status?=pendente {
      values = ["pendente", "aprovada", "rejeitada"]
    }
    int? decidido_por_user_id {
      table = "user"
    }
    timestamp? data_decisao
    text? motivo_decisao filters=trim|max:1000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {
      type : "btree"
      field: [
        {name: "registro_ponto_id", op: "asc"}
        {name: "status", op: "asc"}
      ]
    }
  ]

  guid = "conectahr-correcao-ponto-0001"
}
