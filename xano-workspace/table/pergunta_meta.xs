// Pergunta pre-definida do formulario de metas (change ciclo-de-metas, D2). O RH cria, edita e
// desativa; a resposta guarda o texto da epoca, entao editar aqui nao muda formulario respondido.
table pergunta_meta {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    text texto filters=trim|min:5|max:300
    text? orientacao filters=trim|max:1000
    int ordem?=1
    bool ativa?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "ordem", op: "asc"}]}
  ]
  guid = "OJKiSvU78trmFrz1SgUllTwYN-0"
}
