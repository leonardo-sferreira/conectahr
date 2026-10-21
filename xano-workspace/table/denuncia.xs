// Denuncia do canal de etica (Lei 14.457/2022; change canal-de-denuncias, D1).
// Sem nenhum vinculo com conta ou colaborador: o canal e publico (funciona sem login),
// e quem nao se identifica nao deixa rastro aqui. Sem created_at nem horario: so a data
// (recebida_em), para nao cruzar com registros de acesso. O codigo de acompanhamento so
// existe como hash (codigo_hash, HMAC-SHA256); o texto do codigo vai uma unica vez para
// quem enviou. Quem se identifica escreve o nome e o contato em `identificacao`, que so
// a comissao de etica le.
table denuncia {
  auth = false

  schema {
    int id
    text protocolo filters=trim|max:20
    text codigo_hash filters=trim|max:128
    enum tipo {
      values = ["assedio_moral", "assedio_sexual", "discriminacao", "conduta_antietica", "fraude", "seguranca", "outro"]
    }

    text relato filters=trim|max:4000
    text? quando filters=trim|max:100
    text? envolvidos filters=trim|max:200
    bool identificada?=false
    text? identificacao filters=trim|max:200
    date recebida_em
    enum status?=nova {
      values = ["nova", "em_apuracao", "concluida"]
    }

    enum? resultado {
      values = ["procedente", "improcedente", "inconclusiva"]
    }

    text? parecer filters=trim|max:4000
    date? concluida_em
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "codigo_hash", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]

  guid = "conectahr-denuncia-0001"
}
