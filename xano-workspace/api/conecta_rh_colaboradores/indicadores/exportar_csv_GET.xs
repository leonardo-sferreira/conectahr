// Exporta o painel de indicadores como CSV (item 7.7). Exclusivo de
// RH/ADMIN. Retorna o conteudo CSV como texto no corpo da resposta (o
// cliente/frontend salva o arquivo) — nao ha geracao nativa de arquivo
// fisico a partir de texto neste workspace Xano nem renderizacao de PDF
// (limitacao documentada em docs/indicadores.md); a exportacao PDF fica
// fora do alcance desta camada sem um servico externo de renderizacao.
query "indicadores/exportar_csv" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    date? data_inicio?
    date? data_fim?
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem exportar indicadores."
    }

    function.run "ConectaHR/calcular_indicadores" {
      input = {data_inicio: $input.data_inicio, data_fim: $input.data_fim}
    } as $indicadores

    var $quebra_linha {
      value = "\n"
    }

    var $csv {
      value = ("metrica,valor" ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "periodo_inicio," ~ $indicadores.periodo.data_inicio ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "periodo_fim," ~ $indicadores.periodo.data_fim ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "headcount_ativos," ~ ($indicadores.headcount.ativos|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "headcount_total," ~ ($indicadores.headcount.total|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "admissoes_periodo," ~ ($indicadores.turnover.admissoes_periodo|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "desligamentos_periodo," ~ ($indicadores.turnover.desligamentos_periodo|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "turnover_percentual," ~ ($indicadores.turnover.percentual|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ausencias_aprovadas_periodo," ~ ($indicadores.absenteismo.ausencias_aprovadas_periodo|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "absenteismo_percentual," ~ ($indicadores.absenteismo.percentual|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "horas_extras_periodo," ~ ($indicadores.horas_extras_periodo|to_text) ~ $quebra_linha)
    }

    foreach ($indicadores.distribuicao_departamento) {
      each as $depto_linha {
        var.update $csv {
          value = ($csv ~ "colaboradores_departamento_" ~ $depto_linha.nome ~ "," ~ ($depto_linha.quantidade|to_text) ~ $quebra_linha)
        }
      }
    }

    var.update $csv {
      value = ($csv ~ "ponto_aberto," ~ ($indicadores.ponto.aberto|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ponto_completo," ~ ($indicadores.ponto.completo|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ponto_incompleto," ~ ($indicadores.ponto.incompleto|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ponto_ajustado," ~ ($indicadores.ponto.ajustado|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ferias_pendente," ~ ($indicadores.ferias.pendente|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ferias_aprovada," ~ ($indicadores.ferias.aprovada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ferias_rejeitada," ~ ($indicadores.ferias.rejeitada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ferias_cancelada," ~ ($indicadores.ferias.cancelada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ausencias_pendente," ~ ($indicadores.ausencias.pendente|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ausencias_aprovada," ~ ($indicadores.ausencias.aprovada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "ausencias_rejeitada," ~ ($indicadores.ausencias.rejeitada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "documentos_pendente_analise," ~ ($indicadores.documentos.pendente_analise|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "documentos_aprovado," ~ ($indicadores.documentos.aprovado|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "documentos_vencido," ~ ($indicadores.documentos.vencido|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "documentos_rejeitado," ~ ($indicadores.documentos.rejeitado|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "auditoria_sucesso," ~ ($indicadores.auditoria.sucesso|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "auditoria_falha," ~ ($indicadores.auditoria.falha|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "avaliacoes_pendente," ~ ($indicadores.avaliacoes.pendente|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "avaliacoes_enviada," ~ ($indicadores.avaliacoes.enviada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "metas_planejada," ~ ($indicadores.metas.planejada|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "metas_concluida," ~ ($indicadores.metas.concluida|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "pdis_planejado," ~ ($indicadores.pdis.planejado|to_text) ~ $quebra_linha)
    }

    var.update $csv {
      value = ($csv ~ "pdis_concluido," ~ ($indicadores.pdis.concluido|to_text) ~ $quebra_linha)
    }

    // Auditoria: exportacao de indicadores (item 7.7 e 7.11).
    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "exportar_indicadores_csv"
        recurso      : "indicadores"
        justificativa: ("periodo=" ~ $indicadores.periodo.data_inicio ~ " a " ~ $indicadores.periodo.data_fim)
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    formato : "csv"
    periodo : $indicadores.periodo
    csv     : $csv
  }

  guid = "conectahr-indicadores-exportar-csv-get-0001"
}
