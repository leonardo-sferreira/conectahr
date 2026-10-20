// Ciclo anual de metas (change ciclo-de-metas, D1): tres etapas em janelas de datas iguais para toda
// a empresa (1 definir as metas, 2 registrar o alcancado, 3 fechamento). A etapa esta aberta quando
// inicio <= hoje <= fim; as datas so mudam antes de a etapa 1 abrir.
table ciclo_metas {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int ano
    date etapa1_inicio
    date etapa1_fim
    date etapa2_inicio
    date etapa2_fim
    date etapa3_inicio
    date etapa3_fim
    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ano", op: "asc"}]}
  ]
  guid = "uMRJJ3UDjHSoTC-kwpdLo1v2u-0"
}
