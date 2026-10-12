// Monta o dia de ponto de uma pessoa a partir das marcacoes da ARP e dos tratamentos
// (design D4) e grava o resultado em registro_ponto, que vira um cache do dia lido pela
// Central, pela folha e pelo banco de horas. As quatro primeiras marcacoes validas vao
// para os campos antigos (entrada, inicio e fim do intervalo, saida). Devolve o registro.
function "ConectaHR/atualizar_dia_ponto" {
  input {
    int colaborador_id
    text data
  }

  stack {
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador

    db.query marcacao_ponto {
      where = $db.marcacao_ponto.colaborador_id == $input.colaborador_id && $db.marcacao_ponto.tipo_registro == 7 && $db.marcacao_ponto.data == $input.data
      sort = {marcacao_ponto.nsr: "asc"}
      return = {type: "list"}
    } as $marcacoes

    db.query tratamento_ponto {
      where = $db.tratamento_ponto.colaborador_id == $input.colaborador_id && $db.tratamento_ponto.data == $input.data
      sort = {tratamento_ponto.id: "asc"}
      return = {type: "list"}
    } as $tratamentos

    // Tratamentos anulados por outro tratamento nao valem.
    var $anulados_txt {
      value = ","
    }

    foreach ($tratamentos) {
      each as $t {
        conditional {
          if ($t.anula_tratamento_id != null) {
            var.update $anulados_txt {
              value = $anulados_txt ~ ($t.anula_tratamento_id|to_text) ~ ","
            }
          }
        }
      }
    }

    var $lista_marcacoes {
      value = []
    }

    foreach ($marcacoes) {
      each as $m {
        var.update $lista_marcacoes {
          value = $lista_marcacoes|push:{id: $m.id, ms: $m.data_hora_marcacao}
        }
      }
    }

    var $desconsideradas {
      value = []
    }

    var $inclusoes {
      value = []
    }

    foreach ($tratamentos) {
      each as $t {
        conditional {
          if ($t.anula_tratamento_id == null && ($anulados_txt|contains:("," ~ ($t.id|to_text) ~ ",")) == false && $t.tipo == "desconsideracao" && $t.marcacao_id != null) {
            var.update $desconsideradas {
              value = $desconsideradas|push:$t.marcacao_id
            }
          }
        }

        conditional {
          if ($t.anula_tratamento_id == null && ($anulados_txt|contains:("," ~ ($t.id|to_text) ~ ",")) == false && $t.tipo == "inclusao" && $t.data_hora != null) {
            var.update $inclusoes {
              value = $inclusoes|push:$t.data_hora
            }
          }
        }
      }
    }

    db.query regra_contrato {
      where = $db.regra_contrato.tipo_contrato == $colaborador.tipo_contrato && $db.regra_contrato.ativo == true
      return = {type: "single"}
    } as $regra

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    function.run "ConectaHR/calcular_dia_ponto" {
      input = {marcacoes: $lista_marcacoes, desconsideradas: $desconsideradas, inclusoes: $inclusoes, e_hoje: ($input.data == $hoje), horas_diarias: ($regra != null ? $regra.horas_diarias : null)}
    } as $dia

    var $validas {
      value = $dia.marcacoes
    }

    var $q {
      value = $validas|count
    }

    var $m0 {
      value = ($q > 0 ? ($validas|first).ms : null)
    }

    var $m1 {
      value = ($q > 1 ? ($validas|slice:1:1|first).ms : null)
    }

    var $m2 {
      value = ($q > 2 ? ($validas|slice:2:1|first).ms : null)
    }

    var $m3 {
      value = ($q > 3 ? ($validas|slice:3:1|first).ms : null)
    }

    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $input.colaborador_id && $db.registro_ponto.data == $input.data
      return = {type: "single"}
    } as $registro_existente

    var $registro_id {
      value = 0
    }

    conditional {
      if ($registro_existente == null) {
        db.add registro_ponto {
          data = {
            colaborador_id   : $input.colaborador_id
            data             : $input.data
            hora_entrada     : $m0
            inicio_intervalo : $m1
            fim_intervalo    : $m2
            hora_saida       : $m3
            horas_trabalhadas: $dia.horas_trabalhadas
            horas_extras     : $dia.horas_extras
            status           : $dia.status
            updated_at       : "now"
          }
        } as $novo

        var.update $registro_id {
          value = $novo.id
        }
      }

      else {
        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_existente.id
          data = {
            hora_entrada     : $m0
            inicio_intervalo : $m1
            fim_intervalo    : $m2
            hora_saida       : $m3
            horas_trabalhadas: $dia.horas_trabalhadas
            horas_extras     : $dia.horas_extras
            status           : $dia.status
            updated_at       : "now"
          }
        } as $editado

        var.update $registro_id {
          value = $editado.id
        }
      }
    }

    db.get registro_ponto {
      field_name = "id"
      field_value = $registro_id
    } as $registro
  }

  response = {registro: $registro, quantidade: $q, marcacoes_validas: $validas}

  tags = ["conectahr"]
  guid = "conectahr-atualizar-dia-ponto-0001"
}
