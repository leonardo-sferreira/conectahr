// Calcula o painel de indicadores (item 7.7): colaboradores, ponto,
// ferias, ausencias, documentos, auditoria, avaliacoes, metas, PDIs,
// headcount, turnover, admissoes, desligamentos, absenteismo,
// distribuicao por departamento e horas extras. Reaproveitada por
// `indicadores GET` (painel) e `indicadores/exportar_csv GET`
// (exportacao), para nao duplicar o calculo.
function "ConectaHR/calcular_indicadores" {
  input {
    date? data_inicio?
    date? data_fim?
  }

  stack {
    // Periodo padrao: ultimos 12 meses, quando nao informado. Pre-extrai
    // "now" isolado antes de qualquer aritmetica (ver
    // conectahr-xano-platform-quirks, achado 13).
    var $agora_ts_indicadores {
      value = (now|to_timestamp)
    }

    var $fim_ts {
      value = ($input.data_fim != null ? ($input.data_fim|to_timestamp) : $agora_ts_indicadores)
    }

    var $fim_final {
      value = ($input.data_fim != null ? $input.data_fim : ($agora_ts_indicadores|format_timestamp:"Y-m-d":"UTC"))
    }

    var $inicio_ts_calculado {
      value = ($fim_ts - 31536000000)
    }

    var $inicio_final {
      value = ($input.data_inicio != null ? $input.data_inicio : ($inicio_ts_calculado|format_timestamp:"Y-m-d":"UTC"))
    }

    // ---------- Headcount ----------
    db.query colaborador {
      where = $db.colaborador.status == "Ativo"
      return = {type: "count"}
    } as $headcount_ativos

    db.query colaborador {
      return = {type: "count"}
    } as $headcount_total

    // ---------- Admissoes e desligamentos no periodo ----------
    db.query colaborador {
      where = $db.colaborador.data_admissao != null && $db.colaborador.data_admissao >= $inicio_final && $db.colaborador.data_admissao <= $fim_final
      return = {type: "count"}
    } as $admissoes_periodo

    db.query colaborador {
      where = $db.colaborador.status == "Desligado" && $db.colaborador.data_desligamento != null && $db.colaborador.data_desligamento >= $inicio_final && $db.colaborador.data_desligamento <= $fim_final
      return = {type: "count"}
    } as $desligamentos_periodo

    var $turnover_percentual {
      value = ($headcount_ativos > 0 ? ((($desligamentos_periodo * 100) / $headcount_ativos)|to_int) : 0)
    }

    // ---------- Absenteismo ----------
    db.query ausencia {
      where = $db.ausencia.status == "Aprovada" && $db.ausencia.data_inicio != null && $db.ausencia.data_inicio >= $inicio_final && $db.ausencia.data_inicio <= $fim_final
      return = {type: "count"}
    } as $ausencias_aprovadas_periodo

    var $absenteismo_percentual {
      value = ($headcount_ativos > 0 ? ((($ausencias_aprovadas_periodo * 100) / $headcount_ativos)|to_int) : 0)
    }

    // ---------- Distribuicao por departamento ----------
    db.query departamento {
      where = $db.departamento.ativo == true
      return = {type: "list"}
    } as $departamentos_ativos

    var $distribuicao_departamento {
      value = []
    }

    foreach ($departamentos_ativos) {
      each as $depto_item {
        db.query colaborador {
          where = $db.colaborador.departamento_id == $depto_item.id && $db.colaborador.status == "Ativo"
          return = {type: "count"}
        } as $qtd_no_departamento

        var.update $distribuicao_departamento {
          value = $distribuicao_departamento|push:{departamento_id: $depto_item.id, nome: $depto_item.nome, quantidade: $qtd_no_departamento}
        }
      }
    }

    // ---------- Horas extras no periodo ----------
    db.query registro_ponto {
      where = $db.registro_ponto.data != null && $db.registro_ponto.data >= $inicio_final && $db.registro_ponto.data <= $fim_final && $db.registro_ponto.horas_extras != null
      return = {type: "list"}
    } as $registros_com_horas_extras

    var $total_horas_extras {
      value = 0
    }

    foreach ($registros_com_horas_extras) {
      each as $registro_item {
        var.update $total_horas_extras {
          value = ($total_horas_extras + $registro_item.horas_extras)
        }
      }
    }

    // ---------- Ponto ----------
    db.query registro_ponto {
      where = $db.registro_ponto.status == "Aberto"
      return = {type: "count"}
    } as $ponto_aberto

    db.query registro_ponto {
      where = $db.registro_ponto.status == "Completo"
      return = {type: "count"}
    } as $ponto_completo

    db.query registro_ponto {
      where = $db.registro_ponto.status == "Incompleto"
      return = {type: "count"}
    } as $ponto_incompleto

    db.query registro_ponto {
      where = $db.registro_ponto.status == "Ajustado"
      return = {type: "count"}
    } as $ponto_ajustado

    // ---------- Ferias ----------
    db.query ferias {
      where = $db.ferias.status == "Pendente"
      return = {type: "count"}
    } as $ferias_pendente

    db.query ferias {
      where = $db.ferias.status == "Aprovada"
      return = {type: "count"}
    } as $ferias_aprovada

    db.query ferias {
      where = $db.ferias.status == "Rejeitada"
      return = {type: "count"}
    } as $ferias_rejeitada

    db.query ferias {
      where = $db.ferias.status == "Cancelada"
      return = {type: "count"}
    } as $ferias_cancelada

    // ---------- Ausencias ----------
    db.query ausencia {
      where = $db.ausencia.status == "Pendente"
      return = {type: "count"}
    } as $ausencias_pendente

    db.query ausencia {
      where = $db.ausencia.status == "Aprovada"
      return = {type: "count"}
    } as $ausencias_aprovada

    db.query ausencia {
      where = $db.ausencia.status == "Rejeitada"
      return = {type: "count"}
    } as $ausencias_rejeitada

    // ---------- Documentos ----------
    db.query documento {
      where = $db.documento.status == "pendente_analise"
      return = {type: "count"}
    } as $documentos_pendente_analise

    db.query documento {
      where = $db.documento.status == "aprovado"
      return = {type: "count"}
    } as $documentos_aprovado

    db.query documento {
      where = $db.documento.status == "vencido"
      return = {type: "count"}
    } as $documentos_vencido

    db.query documento {
      where = $db.documento.status == "rejeitado"
      return = {type: "count"}
    } as $documentos_rejeitado

    // ---------- Auditoria ----------
    db.query auditoria {
      where = $db.auditoria.resultado == "sucesso"
      return = {type: "count"}
    } as $auditoria_sucesso

    db.query auditoria {
      where = $db.auditoria.resultado == "falha"
      return = {type: "count"}
    } as $auditoria_falha

    // ---------- Avaliacoes ----------
    db.query avaliacao {
      where = $db.avaliacao.status == "pendente"
      return = {type: "count"}
    } as $avaliacoes_pendente

    db.query avaliacao {
      where = $db.avaliacao.status == "enviada"
      return = {type: "count"}
    } as $avaliacoes_enviada

    // ---------- Metas ----------
    db.query meta_avaliacao {
      where = $db.meta_avaliacao.status == "planejada"
      return = {type: "count"}
    } as $metas_planejada

    db.query meta_avaliacao {
      where = $db.meta_avaliacao.status == "concluida"
      return = {type: "count"}
    } as $metas_concluida

    // ---------- PDIs ----------
    db.query pdi {
      where = $db.pdi.status == "planejado"
      return = {type: "count"}
    } as $pdis_planejado

    db.query pdi {
      where = $db.pdi.status == "concluido"
      return = {type: "count"}
    } as $pdis_concluido
  }

  response = {
    periodo  : {data_inicio: $inicio_final, data_fim: $fim_final}
    headcount: {ativos: $headcount_ativos, total: $headcount_total}
    turnover : {desligamentos_periodo: $desligamentos_periodo, admissoes_periodo: $admissoes_periodo, percentual: $turnover_percentual}
    absenteismo             : {ausencias_aprovadas_periodo: $ausencias_aprovadas_periodo, percentual: $absenteismo_percentual}
    distribuicao_departamento: $distribuicao_departamento
    horas_extras_periodo      : $total_horas_extras
    ponto      : {aberto: $ponto_aberto, completo: $ponto_completo, incompleto: $ponto_incompleto, ajustado: $ponto_ajustado}
    ferias     : {pendente: $ferias_pendente, aprovada: $ferias_aprovada, rejeitada: $ferias_rejeitada, cancelada: $ferias_cancelada}
    ausencias  : {pendente: $ausencias_pendente, aprovada: $ausencias_aprovada, rejeitada: $ausencias_rejeitada}
    documentos : {pendente_analise: $documentos_pendente_analise, aprovado: $documentos_aprovado, vencido: $documentos_vencido, rejeitado: $documentos_rejeitado}
    auditoria  : {sucesso: $auditoria_sucesso, falha: $auditoria_falha}
    avaliacoes : {pendente: $avaliacoes_pendente, enviada: $avaliacoes_enviada}
    metas      : {planejada: $metas_planejada, concluida: $metas_concluida}
    pdis       : {planejado: $pdis_planejado, concluido: $pdis_concluido}
  }

  tags = ["conectahr"]
  guid = "conectahr-calcular-indicadores-0001"
}
