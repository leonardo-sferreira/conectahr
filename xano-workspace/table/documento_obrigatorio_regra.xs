// Matriz de documentos obrigatorios e politica de retencao (item 5.8),
// configuravel por contrato, cargo, departamento e idade (design.md -
// "Documentos e arquivos"/"retencao sera parametrizada..."). Campos
// null nas colunas de aplicabilidade significam "sem restricao nessa
// dimensao" (aplica a todos). `nacionalidade` e `condicao_profissional`
// sao armazenados conforme pedido pelo design.md, mas colaborador nao
// tem campo correspondente para casar automaticamente — aplicabilidade
// por essas duas dimensoes fica registrada, nao avaliada (mesmo gap
// documentado em resolver_regra.xs para categoria_profissional).
table documento_obrigatorio_regra {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
    timestamp? updated_at?

    enum tipo_documento {
      values = ["rg", "cpf", "cin", "cnh", "ctps", "aso_admissional", "laudo_deficiencia", "certificado_profissional", "comprovante_residencia", "comprovante_escolaridade", "registro_profissional", "documentacao_migratoria", "certificado_reservista", "documentacao_responsavel_legal", "outro"]
    }

    enum? tipo_contrato {
      values = ["CLT", "PJ", "ESTAGIO", "APRENDIZ", "TEMPORARIO", "OUTRO"]
    }

    int? cargo_id {
      table = "cargo"
    }
    int? departamento_id {
      table = "departamento"
    }
    int? idade_minima
    int? idade_maxima
    text? nacionalidade filters=trim|max:100
    text? condicao_profissional filters=trim|max:200

    bool exige_frente_verso?=false
    int? prazo_dias_para_envio
    bool obrigatorio?=true

    text? retencao_finalidade filters=trim|max:500
    text? retencao_base_legal filters=trim|max:500
    int? retencao_prazo_dias
    enum? retencao_evento_inicial {
      values = ["data_emissao", "data_validade", "desligamento"]
    }
    enum? retencao_tratamento {
      values = ["anonimizar", "eliminar_automatico", "revisao_manual", "bloqueio_processo"]
    }

    bool ativo?=true
    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "tipo_documento", op: "asc"}]}
    {type: "btree", field: [{name: "ativo", op: "asc"}]}
  ]

  guid = "conectahr-documento-obrigatorio-regra-0001"
}
