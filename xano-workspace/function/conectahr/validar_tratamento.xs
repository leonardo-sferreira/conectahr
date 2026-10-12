// Regras comuns ao pedido de correcao (ponto/correcao) e ao ajuste direto (folha_ponto/tratar)
// no REP-P (change ponto-rep-p-e-ferias-clt). Recusa com mensagem clara:
//   inclusao: horario fora do dia (de 00:00 ate as 06:00 do dia seguinte, Brasilia) ou no
//             futuro;
//   desconsideracao: marcacao que nao existe, de outra pessoa ou de outro dia, ja
//             desconsiderada ou com pedido pendente.
//   alteracao: as duas regras (a marcacao a corrigir e o horario certo).
//   Com tratamento_id (marcacao incluida), a marcacao e essa inclusao: valida, do dia, nao desfeita
//   e sem pedido pendente.
function "ConectaHR/validar_tratamento" {
  input {
    int colaborador_id
    text data
    text tipo
    int? marcacao_id?
    int? tratamento_id?
    timestamp? data_hora?
  }

  stack {
    precondition ($input.tipo == "inclusao" || $input.tipo == "desconsideracao" || $input.tipo == "alteracao") {
      error_type = "inputerror"
      error = "Escolha incluir, corrigir o horario ou desconsiderar uma marcacao."
    }

    conditional {
      if ($input.tipo == "inclusao" || $input.tipo == "alteracao") {
        precondition ($input.data_hora != null) {
          error_type = "inputerror"
          error = ($input.tipo == "alteracao" ? "Informe o horario certo da marcacao." : "Informe o horario da marcacao que faltou.")
        }

        // Meia-noite de Brasilia = 03:00 UTC; a janela vai ate as 06:00 do dia seguinte.
        var $inicio_janela {
          value = ($input.data|to_timestamp) + 10800000
        }

        var $fim_janela {
          value = $inicio_janela + 86400000 + 21600000
        }

        precondition ($input.data_hora >= $inicio_janela && $input.data_hora <= $fim_janela) {
          error_type = "inputerror"
          error = "O horario pedido precisa ser do mesmo dia."
        }

        precondition ($input.data_hora <= now) {
          error_type = "inputerror"
          error = "O horario pedido nao pode ser no futuro."
        }
      }
    }

    conditional {
      if (($input.tipo == "desconsideracao" || $input.tipo == "alteracao") && $input.tratamento_id != null) {
        // Marcacao incluida por tratamento: so uma inclusao valida, da pessoa e do dia, ainda nao
        // desfeita e sem outro pedido em analise.
        db.get tratamento_ponto {
          field_name = "id"
          field_value = $input.tratamento_id
        } as $inclusao_alvo

        precondition ($inclusao_alvo != null && $inclusao_alvo.tipo == "inclusao" && $inclusao_alvo.anula_tratamento_id == null && $inclusao_alvo.colaborador_id == $input.colaborador_id && ($inclusao_alvo.data|format_timestamp:"Y-m-d":"UTC") == $input.data) {
          error_type = "inputerror"
          error = "A marcacao escolhida nao e deste dia."
        }

        db.query tratamento_ponto {
          where = $db.tratamento_ponto.anula_tratamento_id == $input.tratamento_id
          return = {type: "single"}
        } as $ja_desfeita

        precondition ($ja_desfeita == null) {
          error_type = "inputerror"
          error = "Esta marcacao ja foi desconsiderada."
        }

        db.query correcao_ponto {
          where = $db.correcao_ponto.tratamento_id == $input.tratamento_id && $db.correcao_ponto.status == "pendente"
          return = {type: "single"}
        } as $pedido_pendente_inclusao

        precondition ($pedido_pendente_inclusao == null) {
          error_type = "inputerror"
          error = "Ja existe um pedido em analise para esta marcacao."
        }
      }
    }

    conditional {
      if (($input.tipo == "desconsideracao" || $input.tipo == "alteracao") && $input.tratamento_id == null) {
        precondition ($input.marcacao_id != null) {
          error_type = "inputerror"
          error = ($input.tipo == "alteracao" ? "Escolha a marcacao a corrigir." : "Escolha a marcacao a desconsiderar.")
        }

        db.get marcacao_ponto {
          field_name = "id"
          field_value = $input.marcacao_id
        } as $marcacao

        precondition ($marcacao != null && $marcacao.tipo_registro == 7 && $marcacao.colaborador_id == $input.colaborador_id && ($marcacao.data|format_timestamp:"Y-m-d":"UTC") == $input.data) {
          error_type = "inputerror"
          error = "A marcacao escolhida nao e deste dia."
        }

        db.query tratamento_ponto {
          where = $db.tratamento_ponto.marcacao_id == $input.marcacao_id && $db.tratamento_ponto.tipo == "desconsideracao" && $db.tratamento_ponto.anula_tratamento_id == null
          return = {type: "single"}
        } as $ja_desconsiderada

        precondition ($ja_desconsiderada == null) {
          error_type = "inputerror"
          error = "Esta marcacao ja foi desconsiderada."
        }

        db.query correcao_ponto {
          where = $db.correcao_ponto.marcacao_id == $input.marcacao_id && $db.correcao_ponto.status == "pendente"
          return = {type: "single"}
        } as $pedido_pendente

        precondition ($pedido_pendente == null) {
          error_type = "inputerror"
          error = "Ja existe um pedido em analise para esta marcacao."
        }
      }
    }
  }

  response = true

  tags = ["conectahr"]
  guid = "conectahr-validar-tratamento-0001"
}
