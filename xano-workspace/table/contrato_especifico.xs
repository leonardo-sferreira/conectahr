// Metadados especificos por tipo de contrato nao-CLT (item 3.6):
// estagio, aprendiz, temporario e PJ. Um registro por colaborador.
// CLT usa os campos padrao de colaborador/historico_profissional e o
// rastreio eSocial/CTPS (item 3.5) — nao passa por aqui.
table contrato_especifico {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?

    int colaborador_id {
      table = "colaborador"
    }

    enum tipo_contrato {
      values = ["ESTAGIO", "APRENDIZ", "TEMPORARIO", "PJ"]
    }

    enum status?=rascunho {
      values = ["rascunho", "ativo"]
    }

    // Estagio: termo de compromisso, estudante, instituicao de ensino,
    // jornada e recesso — sem classificar o estagiario como CLT.
    text? estagio_instituicao_ensino filters=trim|max:150
    text? estagio_curso filters=trim|max:150
    bool? estagio_termo_compromisso_valido?=false
    date? estagio_termo_compromisso_data
    decimal? estagio_jornada_semanal_maxima
    int? estagio_recesso_dias_disponivel

    // Aprendiz: programa, soma de horas praticas/teoricas e o limite de
    // jornada aplicavel ao contrato/programa.
    text? aprendiz_programa filters=trim|max:150
    decimal? aprendiz_horas_praticas_semanais
    decimal? aprendiz_horas_teoricas_semanais
    decimal? aprendiz_jornada_maxima_semanal

    // Temporario: contrato escrito, empresa, tomadora, motivo, prazo e
    // prorrogacoes.
    text? temporario_empresa filters=trim|max:150
    text? temporario_tomadora filters=trim|max:150
    text? temporario_motivo filters=trim|max:500
    date? temporario_data_prazo
    int? temporario_prorrogacoes?=0

    // PJ: nao recebe automaticamente jornada/ponto/ferias/subordinacao —
    // mantem contrato comercial, entregas, vigencia e condicoes.
    text? pj_contrato_numero filters=trim|max:100
    text? pj_entregas filters=trim|max:2000
    date? pj_vigencia_inicio
    date? pj_vigencia_fim
    text? pj_condicoes_comerciais filters=trim|max:2000

    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "colaborador_id", op: "asc"}]}
    {type: "btree", field: [{name: "tipo_contrato", op: "asc"}]}
  ]

  guid = "conectahr-contrato-especifico-0001"
}
