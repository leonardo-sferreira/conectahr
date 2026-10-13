table cargo {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    text nome filters=trim|max:100|min:2
    text descricao? filters=trim
    decimal salario_base?
    bool ativo?=true

    // Nivel hierarquico do cargo (change organograma-hierarquia, D2): ordena e rotula as pessoas no
    // organograma. Opcional; cargo sem nivel aparece depois dos que tem.
    int? nivel_hierarquico_id? {
      table = "nivel_hierarquico"
    }

    // Senioridade e departamento do cargo (change cadastro-de-cargos, D1 e D3). O nome continua sendo
    // o titulo completo, como vai para a carteira ("Desenvolvedor Front-end Pleno"); a senioridade fica
    // separada para filtrar e rotular. Cargo sem departamento serve a qualquer departamento.
    enum? senioridade? {
      values = ["junior", "pleno", "senior", "especialista"]
    }

    int? departamento_id? {
      table = "departamento"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "nome", op: "asc"}]}
  ]

  guid = "5gK8xV8e14N8eSU0GzGCFv07FYg"
}