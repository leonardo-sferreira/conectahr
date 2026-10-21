// Conversa entre quem denunciou (pelo codigo) e a comissao de etica (change
// canal-de-denuncias, D1). Sem conta de quem escreveu: o lado e so "denunciante" ou
// "comissao" (quem da comissao escreveu fica na auditoria). So a data, sem horario.
table denuncia_mensagem {
  auth = false

  schema {
    int id
    int denuncia_id {
      table = "denuncia"
    }

    enum autor {
      values = ["denunciante", "comissao"]
    }

    text texto filters=trim|max:2000
    date enviada_em
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "denuncia_id", op: "asc"}]}
  ]

  guid = "conectahr-denuncia-mensagem-0001"
}
