// Semeia o catalogo de parametros protegidos (item 1.10): para cada
// parametro que `regra_override` pode alterar, define se e livremente
// `configuravel` pelo RH, exige aprovacao (`configuravel_com_aprovacao`,
// via instrumento_normativo) ou nunca pode ser sobrescrito
// (`sem_override`). Idempotente no nivel do lote inteiro: so semeia se
// a tabela ainda estiver vazia. Sem input - roda uma vez via
// `xano function run`.
//
// Criterio adotado (decisao de produto, ajustavel editando os dados):
// parametros com impacto direto em limites legais de jornada, horas
// extras, banco de horas e ferias exigem aprovacao formal; controle de
// ponto nunca pode ser desativado por override (requisito de
// conformidade); os demais (antecedencia e fracionamento de ferias)
// sao configuraveis diretamente pelo RH.
function "ConectaHR/semear_parametros_protegidos" {
  input {
  }

  stack {
    db.query parametro_protegido {
      return = {type: "list"}
    } as $existentes

    var $inseridos {
      value = []
    }

    conditional {
      if (($existentes|count) == 0) {
        db.add parametro_protegido {
          data = {parametro: "horas_diarias", nivel_protecao: "configuravel_com_aprovacao", descricao: "Limite legal de jornada diaria."}
        } as $p1

        db.add parametro_protegido {
          data = {parametro: "horas_semanais", nivel_protecao: "configuravel_com_aprovacao", descricao: "Limite legal de jornada semanal."}
        } as $p2

        db.add parametro_protegido {
          data = {parametro: "intervalo_minutos", nivel_protecao: "configuravel_com_aprovacao", descricao: "Intervalo intrajornada minimo."}
        } as $p3

        db.add parametro_protegido {
          data = {parametro: "permite_hora_extra", nivel_protecao: "configuravel_com_aprovacao", descricao: "Autorizacao para realizar horas extras."}
        } as $p4

        db.add parametro_protegido {
          data = {parametro: "limite_hora_extra_diaria", nivel_protecao: "configuravel_com_aprovacao", descricao: "Limite diario de horas extras."}
        } as $p5

        db.add parametro_protegido {
          data = {parametro: "permite_banco_horas", nivel_protecao: "configuravel_com_aprovacao", descricao: "Autorizacao para banco de horas."}
        } as $p6

        db.add parametro_protegido {
          data = {parametro: "prazo_compensacao_banco_horas", nivel_protecao: "configuravel_com_aprovacao", descricao: "Prazo para compensar o banco de horas."}
        } as $p7

        db.add parametro_protegido {
          data = {parametro: "controle_ponto", nivel_protecao: "sem_override", descricao: "Obrigatoriedade de registro de ponto - requisito de conformidade, nunca desativavel por override."}
        } as $p8

        db.add parametro_protegido {
          data = {parametro: "dias_ferias", nivel_protecao: "configuravel_com_aprovacao", descricao: "Quantidade de dias de ferias ou recesso."}
        } as $p9

        db.add parametro_protegido {
          data = {parametro: "permite_fracionamento", nivel_protecao: "configuravel", descricao: "Autorizacao para fracionar as ferias."}
        } as $p10

        db.add parametro_protegido {
          data = {parametro: "maximo_periodos", nivel_protecao: "configuravel_com_aprovacao", descricao: "Quantidade maxima de periodos de fracionamento."}
        } as $p11

        db.add parametro_protegido {
          data = {parametro: "minimo_periodo_principal", nivel_protecao: "configuravel_com_aprovacao", descricao: "Duracao minima do periodo principal de ferias."}
        } as $p12

        db.add parametro_protegido {
          data = {parametro: "minimo_outros_periodos", nivel_protecao: "configuravel_com_aprovacao", descricao: "Duracao minima dos demais periodos de ferias."}
        } as $p13

        db.add parametro_protegido {
          data = {parametro: "antecedencia_ferias", nivel_protecao: "configuravel", descricao: "Antecedencia minima para solicitar ferias."}
        } as $p14

        db.add parametro_protegido {
          data = {parametro: "permite_solicitacao_ferias", nivel_protecao: "configuravel_com_aprovacao", descricao: "Autorizacao para o colaborador solicitar ferias pelo sistema."}
        } as $p15

        var.update $inseridos {
          value = ["horas_diarias", "horas_semanais", "intervalo_minutos", "permite_hora_extra", "limite_hora_extra_diaria", "permite_banco_horas", "prazo_compensacao_banco_horas", "controle_ponto", "dias_ferias", "permite_fracionamento", "maximo_periodos", "minimo_periodo_principal", "minimo_outros_periodos", "antecedencia_ferias", "permite_solicitacao_ferias"]
        }
      }
    }

    db.query parametro_protegido {
      sort = {parametro_protegido.parametro: "asc"}
      return = {type: "list"}
    } as $catalogo_final
  }

  response = {
    sucesso  : true
    inseridos: $inseridos
    catalogo : $catalogo_final
  }

  tags = ["conectahr"]
  guid = "conectahr-semear-parametros-protegidos-0001"
}
