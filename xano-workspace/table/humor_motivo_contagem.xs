// Termometro de humor (change termometro-de-humor, D2): contagem anonima do motivo opcional ("o que mais
// pesou"), por (ciclo, departamento, motivo). Contado a parte da nota, para nao ligar uma coisa a outra.
// Sem pessoa, data ou horario.
table humor_motivo_contagem {
  auth = false

  schema {
    int id
    int ciclo
    int departamento_id?=0
    enum motivo {
      values = ["carga_trabalho", "reconhecimento", "lideranca", "colegas", "comunicacao", "estrutura"]
    }

    int quantidade?=0
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "ciclo", op: "asc"}, {name: "departamento_id", op: "asc"}, {name: "motivo", op: "asc"}]}
  ]

  guid = "conectahr-humor-motivo-contagem-0001"
}
