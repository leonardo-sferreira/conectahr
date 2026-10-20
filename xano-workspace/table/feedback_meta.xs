// Feedback do superior direto ou do gestor do departamento numa etapa enviada do formulario de
// metas (change ciclo-de-metas, D4). So inclusao: nao se edita nem se apaga.
table feedback_meta {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int formulario_meta_id {
      table = "formulario_meta"
    }

    int etapa filters=min:1|max:3
    int autor_user_id {
      table = "user"
    }

    text texto filters=trim|min:5|max:2000
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "formulario_meta_id", op: "asc"}]}
  ]
  guid = "7BT2KKs5Ra5zzZMG3HcH0DGaF-0"
}
