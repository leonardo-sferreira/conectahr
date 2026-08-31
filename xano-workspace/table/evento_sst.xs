// Metadados de ASO/PCMSO/eventos de SST - NUNCA um prontuario medico
// comum. So guarda o resultado operacional (apto/inapto/apto com
// restricao) e prazos, sem campo de diagnostico ou historico clinico
// em texto livre. O arquivo do exame (quando anexado) fica protegido
// como qualquer documento, mas o registro operacional aqui e o que o
// sistema usa para decisoes de acesso/exibicao.
table evento_sst {
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
    enum tipo {
      values = ["aso_admissional", "aso_periodico", "aso_demissional", "aso_mudanca_funcao", "pcmso_prazo", "outro_sst"]
    }
    enum? resultado {
      values = ["apto", "inapto", "apto_com_restricao"]
    }
    date data_exame
    date? data_validade
    text? medico_responsavel filters=trim|max:200
    text? documento_url filters=trim|max:500
    text? observacao_operacional filters=trim|max:300
    int registrado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "colaborador_id", op: "asc"}]}
  ]

  guid = "conectahr-evento-sst-0001"
}
