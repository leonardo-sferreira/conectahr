// Grava um registro na ARP do REP-P (marcacao_ponto), com o proximo NSR da empresa
// (Portaria MTP 671/2021, Anexo IX, item 6). Tipos: 2 empregador, 5 empregado, 6 evento
// sensivel, 7 marcacao. No tipo 7 calcula o hash SHA-256 encadeado com o registro 7
// anterior (ConectaHR/hash_registro_rep). O indice unico em nsr impede NSR repetido:
// numa colisao, a gravacao falha e quem chamou tenta de novo (design D2).
function "ConectaHR/gravar_registro_rep" {
  input {
    int tipo_registro
    int? colaborador_id?
    text? cpf?
    timestamp? momento_marcacao?
    text? cpf_responsavel?
    int? responsavel_user_id?
    json? dados?
  }

  stack {
    var $agora {
      value = now
    }

    function.run "ConectaHR/data_hora_afd" {
      input = {momento: $agora}
    } as $gravacao_txt

    db.query marcacao_ponto {
      sort = {marcacao_ponto.nsr: "desc"}
      return = {type: "single"}
    } as $ultimo

    var $nsr {
      value = ($ultimo != null ? $ultimo.nsr : 0) + 1
    }

    var $momento {
      value = ($input.momento_marcacao != null ? $input.momento_marcacao : $agora)
    }

    var $marcacao_txt {
      value = null
    }

    var $hash {
      value = null
    }

    var $hash_anterior {
      value = null
    }

    var $cpf_digitos {
      value = ($input.cpf != null ? $input.cpf : "")
    }

    conditional {
      if ($input.tipo_registro == 7) {
        function.run "ConectaHR/data_hora_afd" {
          input = {momento: $momento}
        } as $marcacao_formatada

        var.update $marcacao_txt {
          value = $marcacao_formatada
        }

        db.query marcacao_ponto {
          where = $db.marcacao_ponto.tipo_registro == 7
          sort = {marcacao_ponto.nsr: "desc"}
          return = {type: "single"}
        } as $ultimo_tipo7

        var.update $hash_anterior {
          value = ($ultimo_tipo7 != null ? $ultimo_tipo7.hash : null)
        }

        function.run "ConectaHR/hash_registro_rep" {
          input = {nsr: $nsr, data_hora_marcacao_txt: $marcacao_formatada, cpf: $cpf_digitos, data_hora_gravacao_txt: $gravacao_txt, coletor: "02", offline: false, hash_anterior: $hash_anterior}
        } as $calculo

        var.update $hash {
          value = $calculo.hash
        }
      }
    }

    db.add marcacao_ponto {
      data = {
        nsr                   : $nsr
        tipo_registro         : $input.tipo_registro
        colaborador_id        : $input.colaborador_id
        cpf                   : $input.cpf
        data_hora_marcacao    : ($input.tipo_registro == 7 ? $momento : null)
        data                  : ($input.tipo_registro == 7 ? ($momento|format_timestamp:"Y-m-d":"America/Sao_Paulo") : null)
        data_hora_marcacao_txt: $marcacao_txt
        data_hora_gravacao    : $agora
        data_hora_gravacao_txt: $gravacao_txt
        coletor               : ($input.tipo_registro == 7 ? "02" : null)
        offline               : false
        hash                  : $hash
        hash_anterior         : $hash_anterior
        cpf_responsavel       : $input.cpf_responsavel
        responsavel_user_id   : $input.responsavel_user_id
        dados                 : $input.dados
      }
    } as $registro
  }

  response = $registro

  tags = ["conectahr"]
  guid = "conectahr-gravar-registro-rep-0001"
}
