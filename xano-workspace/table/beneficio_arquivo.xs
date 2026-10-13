// Materiais de um beneficio para leitura geral (change apresentacao-de-beneficios, D1): guia do plano, tabela de
// rede credenciada etc. O arquivo fica no bucket privado do Supabase (caminho beneficios/<uuid>.<ext>) e abre por
// link assinado. Remover desativa, sem apagar o registro.
table beneficio_arquivo {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    int beneficio_id {
      table = "beneficio"
    }

    text nome filters=trim|min:2|max:100
    text caminho filters=trim|max:200
    bool ativo?=true
    int? criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "beneficio_id", op: "asc"}]}
  ]

  guid = "conectahr-beneficio-arquivo-0001"
}
