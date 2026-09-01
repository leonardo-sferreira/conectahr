// Painel de indicadores (item 7.7). Exclusivo de RH/ADMIN. Calculo
// delegado a ConectaHR/calcular_indicadores, reaproveitada tambem pela
// exportacao CSV.
query indicadores verb=GET {
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
      error = "Somente RH ou ADMIN podem consultar indicadores."
    }

    function.run "ConectaHR/calcular_indicadores" {
      input = {data_inicio: $input.data_inicio, data_fim: $input.data_fim}
    } as $indicadores

    // Auditoria: consulta de indicadores (item 7.11).
    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "consultar_indicadores"
        recurso      : "indicadores"
        justificativa: ("periodo=" ~ $indicadores.periodo.data_inicio ~ " a " ~ $indicadores.periodo.data_fim)
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    periodo    : $indicadores.periodo
    headcount  : $indicadores.headcount
    turnover   : $indicadores.turnover
    absenteismo: $indicadores.absenteismo
    distribuicao_departamento: $indicadores.distribuicao_departamento
    horas_extras_periodo     : $indicadores.horas_extras_periodo
    ponto      : $indicadores.ponto
    ferias     : $indicadores.ferias
    ausencias  : $indicadores.ausencias
    documentos : $indicadores.documentos
    auditoria  : $indicadores.auditoria
    avaliacoes : $indicadores.avaliacoes
    metas      : $indicadores.metas
    pdis       : $indicadores.pdis
  }

  guid = "conectahr-indicadores-get-0001"
}
