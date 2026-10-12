// Tratamento das marcacoes (Portaria MTP 671/2021, art. 82, paragrafo unico): so
// acrescenta informacao, sem alterar a ARP (marcacao_ponto). Incluir uma marcacao que
// faltou ou desconsiderar uma marcacao indevida, sempre com motivo e autor. Nasce de um
// pedido de correcao aprovado ou de um ajuste direto de quem decide pela hierarquia.
// Nao tem edicao: desfazer cria outro tratamento, que aponta para o anulado.
table tratamento_ponto {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int colaborador_id {
      table = "colaborador"
    }

    date data
    enum tipo {
      values = ["inclusao", "desconsideracao"]
    }

    // Desconsideracao: a marcacao da ARP desconsiderada.
    int? marcacao_id {
      table = "marcacao_ponto"
    }

    // Inclusao: a data e hora incluida.
    timestamp? data_hora
    text motivo filters=trim|min:5|max:150
    int autor_user_id {
      table = "user"
    }

    int? correcao_ponto_id {
      table = "correcao_ponto"
    }

    // Quando este tratamento desfaz outro.
    int? anula_tratamento_id {
      table = "tratamento_ponto"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "data", op: "asc"}
      ]
    }
    {type: "btree", field: [{name: "marcacao_id", op: "asc"}]}
  ]

  guid = "conectahr-tratamento-ponto-0001"
}
