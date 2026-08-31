// RH/ADMIN ativa um contrato especifico apos as validacoes do tipo
// (item 3.6). Estagio sem termo de compromisso valido, ou aprendiz com
// jornada acima do limite do programa, bloqueiam a ativacao.
query "contratos_especificos/{id}/ativar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh

    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }

    precondition ($perfil_rh == "RH" || $perfil_rh == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem ativar contratos especificos."
    }

    db.get contrato_especifico {
      field_name = "id"
      field_value = $input.id
    } as $contrato_atual

    precondition ($contrato_atual != null) {
      error_type = "notfound"
      error = "Contrato especifico nao encontrado."
    }

    precondition ($contrato_atual.status == "rascunho") {
      error_type = "inputerror"
      error = "Somente contratos em rascunho podem ser ativados."
    }

    // Estagio: exige termo de compromisso valido — sem isso e uma
    // pendencia documental, nao um erro de validacao generico.
    conditional {
      if ($contrato_atual.tipo_contrato == "ESTAGIO") {
        precondition ($contrato_atual.estagio_termo_compromisso_valido == true) {
          error_type = "inputerror"
          error = "Nao e possivel ativar o estagio sem um termo de compromisso valido. Pendencia documental."
        }
      }
    }

    // Aprendiz: soma de horas praticas e teoricas nao pode exceder a
    // jornada maxima do programa/contrato.
    conditional {
      if ($contrato_atual.tipo_contrato == "APRENDIZ") {
        precondition ($contrato_atual.aprendiz_horas_praticas_semanais != null && $contrato_atual.aprendiz_horas_teoricas_semanais != null && $contrato_atual.aprendiz_jornada_maxima_semanal != null) {
          error_type = "inputerror"
          error = "Preencha horas praticas, teoricas e a jornada maxima do aprendiz antes de ativar."
        }

        var $carga_total_aprendiz {
          value = $contrato_atual.aprendiz_horas_praticas_semanais + $contrato_atual.aprendiz_horas_teoricas_semanais
        }

        precondition ($carga_total_aprendiz <= $contrato_atual.aprendiz_jornada_maxima_semanal) {
          error_type = "inputerror"
          error = "A soma das horas praticas e teoricas excede a jornada maxima permitida para o programa."
        }
      }
    }

    // Temporario: contrato escrito exige empresa, tomadora, motivo e prazo.
    conditional {
      if ($contrato_atual.tipo_contrato == "TEMPORARIO") {
        precondition ($contrato_atual.temporario_empresa != null && $contrato_atual.temporario_tomadora != null && $contrato_atual.temporario_motivo != null && $contrato_atual.temporario_data_prazo != null) {
          error_type = "inputerror"
          error = "Preencha empresa, tomadora, motivo e prazo do contrato temporario antes de ativar."
        }
      }
    }

    // PJ: mantem contrato, vigencia e condicoes comerciais — nao recebe
    // automaticamente jornada, ponto, ferias ou subordinacao.
    conditional {
      if ($contrato_atual.tipo_contrato == "PJ") {
        precondition ($contrato_atual.pj_contrato_numero != null && $contrato_atual.pj_vigencia_inicio != null && $contrato_atual.pj_vigencia_fim != null) {
          error_type = "inputerror"
          error = "Preencha numero do contrato e vigencia do PJ antes de ativar."
        }

        precondition ($contrato_atual.pj_vigencia_fim >= $contrato_atual.pj_vigencia_inicio) {
          error_type = "inputerror"
          error = "A vigencia final do contrato PJ nao pode ser anterior ao inicio."
        }
      }
    }

    db.edit contrato_especifico {
      field_name = "id"
      field_value = $contrato_atual.id
      data = {status: "ativo", updated_at: "now"}
    } as $contrato_ativado

    db.add auditoria {
      data = {
        user_id    : $usuario_rh.id
        acao       : "ativar_contrato_especifico"
        recurso    : "contrato_especifico"
        registro_id: $contrato_atual.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Contrato especifico ativado com sucesso."
    contrato : $contrato_ativado
  }

  guid = "conectahr-contratos-especificos-ativar-post-0001"
}
