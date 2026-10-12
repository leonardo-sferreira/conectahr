// Armazenamento de Registro de Ponto (ARP) do REP-P (Portaria MTP 671/2021, Anexo IX,
// itens 6, 7 e 10). So de inclusao: nenhum endpoint, rotina ou anonimizacao edita ou
// apaga esta tabela (tools/checar_endpoints.py confere). Guarda os registros que vao
// para o AFD, numa sequencia unica de NSR da empresa:
//   2 = inclusao ou alteracao do empregador; 5 = inclusao, alteracao ou exclusao de
//   empregado; 6 = evento sensivel (07 disponibilidade, 08 indisponibilidade);
//   7 = marcacao de ponto.
// Os campos *_txt guardam a data e hora exatamente como saem no AFD (formato DH,
// "AAAA-MM-ddThh:mm:00-0300"), para que o hash seja recalculado igual (design D3).
// O hash do tipo 7 e o SHA-256 dos campos 1 a 7 do registro, como no AFD, mais o hash
// do registro 7 anterior.
table marcacao_ponto {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int nsr
    int tipo_registro
    int? colaborador_id {
      table = "colaborador"
    }

    // CPF do trabalhador (tipos 5 e 7), so digitos.
    text? cpf filters=trim|max:11
    timestamp? data_hora_marcacao
    // Dia da marcacao no horario de Brasilia (para montar o dia; nao vai para o AFD).
    date? data
    text? data_hora_marcacao_txt filters=trim|max:24
    timestamp data_hora_gravacao
    text data_hora_gravacao_txt filters=trim|max:24
    // "02" = navegador (unico coletor do ConectaRH).
    text? coletor filters=trim|max:2
    bool offline?=false
    text? hash filters=trim|max:64
    text? hash_anterior filters=trim|max:64
    // Quem fez a operacao (tipos 2, 5 e 6): CPF, so digitos, e o usuario.
    text? cpf_responsavel filters=trim|max:11
    int? responsavel_user_id {
      table = "user"
    }

    // Demais campos do registro no AFD (tipo 2: empregador; tipo 5: operacao e nome;
    // tipo 6: codigo do evento).
    json? dados
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "nsr", op: "asc"}]}
    {type: "btree", field: [{name: "tipo_registro", op: "asc"}]}
    {
      type : "btree"
      field: [
        {name: "colaborador_id", op: "asc"}
        {name: "data", op: "asc"}
      ]
    }
    {type: "btree", field: [{name: "data_hora_gravacao", op: "asc"}]}
  ]

  guid = "conectahr-marcacao-ponto-0001"
}
