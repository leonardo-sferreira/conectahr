// Plano de acao dos riscos psicossociais (NR-1; change riscos-psicossociais, D3): a medida para
// um risco de um setor numa avaliacao, com responsavel, prazo e situacao. Entra no relatorio do
// PGR com o inventario de riscos. departamento_id = 0 significa a empresa inteira.
table acao_psicossocial {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int pesquisa_clima_id {
      table = "pesquisa_clima"
    }

    int departamento_id?=0
    text dimensao filters=trim|max:60
    text? nivel_risco filters=trim|max:20
    text medida filters=trim|max:1000
    text responsavel filters=trim|max:150
    date prazo
    enum status?=planejada {
      values = ["planejada", "em_andamento", "concluida", "cancelada"]
    }

    date? concluida_em
    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "pesquisa_clima_id", op: "asc"}]}
  ]

  guid = "conectahr-acao-psicossocial-0001"
}
