// Dados do empregador e do REP-P (Portaria MTP 671/2021): uma linha so. Usados no
// comprovante de registro de ponto (art. 79), no espelho (art. 84), no AFD (registros 1
// e 2) e no AEJ (registros 01, 02 e 08). Cada alteracao dos dados do empregador gera um
// registro tipo 2 na ARP (marcacao_ponto). Sem esta linha, o ponto nao e marcado.
table empregador {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    enum tipo_identificador?=cnpj {
      values = ["cnpj", "cpf"]
    }

    // CNPJ (14) ou CPF (11), so digitos.
    text identificador filters=trim|max:14
    // CNO ou CAEPF, quando houver, so digitos.
    text? cno_caepf filters=trim|max:14
    text razao_social filters=trim|min:2|max:150
    text local_prestacao filters=trim|min:2|max:100
    // Numero de registro do programa no INPI (17 posicoes no AFD).
    text? inpi_registro filters=trim|max:17
    enum desenvolvedor_tipo_identificador?=cnpj {
      values = ["cnpj", "cpf"]
    }

    text? desenvolvedor_identificador filters=trim|max:14
    text? desenvolvedor_nome filters=trim|max:150
    text? desenvolvedor_email filters=trim|max:50
    text? ptrp_nome filters=trim|max:150
    text? ptrp_versao filters=trim|max:8
    // Disponibilidade do servico de ponto (registros tipo 6, eventos 07 e 08).
    bool servico_disponivel?=true
    int? atualizado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
  ]

  guid = "conectahr-empregador-0001"
}
