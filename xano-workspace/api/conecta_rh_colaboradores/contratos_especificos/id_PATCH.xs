// RH/ADMIN preenche os campos especificos do tipo de contrato de um
// registro contrato_especifico (item 3.6). So os campos do proprio tipo
// tem efeito pratico na ativacao — os demais ficam gravados mas
// ignorados pelas validacoes de contratos_especificos/{id}/ativar.
query "contratos_especificos/{id}" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    text? estagio_instituicao_ensino? filters=trim|max:150
    text? estagio_curso? filters=trim|max:150
    bool? estagio_termo_compromisso_valido?
    date? estagio_termo_compromisso_data?
    decimal? estagio_jornada_semanal_maxima?
    int? estagio_recesso_dias_disponivel?
    text? aprendiz_programa? filters=trim|max:150
    decimal? aprendiz_horas_praticas_semanais?
    decimal? aprendiz_horas_teoricas_semanais?
    decimal? aprendiz_jornada_maxima_semanal?
    text? temporario_empresa? filters=trim|max:150
    text? temporario_tomadora? filters=trim|max:150
    text? temporario_motivo? filters=trim|max:500
    date? temporario_data_prazo?
    int? temporario_prorrogacoes?
    text? pj_contrato_numero? filters=trim|max:100
    text? pj_entregas? filters=trim|max:2000
    date? pj_vigencia_inicio?
    date? pj_vigencia_fim?
    text? pj_condicoes_comerciais? filters=trim|max:2000
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
      error = "Somente RH ou ADMIN podem atualizar contratos especificos."
    }

    db.get contrato_especifico {
      field_name = "id"
      field_value = $input.id
    } as $contrato_atual

    precondition ($contrato_atual != null) {
      error_type = "notfound"
      error = "Contrato especifico nao encontrado."
    }

    // Preserva o valor atual de cada campo quando nao informado.
    var $estagio_instituicao_final {
      value = ($input.estagio_instituicao_ensino != null ? $input.estagio_instituicao_ensino : $contrato_atual.estagio_instituicao_ensino)
    }

    var $estagio_curso_final {
      value = ($input.estagio_curso != null ? $input.estagio_curso : $contrato_atual.estagio_curso)
    }

    var $estagio_termo_valido_final {
      value = ($input.estagio_termo_compromisso_valido != null ? $input.estagio_termo_compromisso_valido : $contrato_atual.estagio_termo_compromisso_valido)
    }

    var $estagio_termo_data_final {
      value = ($input.estagio_termo_compromisso_data != null ? $input.estagio_termo_compromisso_data : $contrato_atual.estagio_termo_compromisso_data)
    }

    var $estagio_jornada_final {
      value = ($input.estagio_jornada_semanal_maxima != null ? $input.estagio_jornada_semanal_maxima : $contrato_atual.estagio_jornada_semanal_maxima)
    }

    var $estagio_recesso_final {
      value = ($input.estagio_recesso_dias_disponivel != null ? $input.estagio_recesso_dias_disponivel : $contrato_atual.estagio_recesso_dias_disponivel)
    }

    var $aprendiz_programa_final {
      value = ($input.aprendiz_programa != null ? $input.aprendiz_programa : $contrato_atual.aprendiz_programa)
    }

    var $aprendiz_praticas_final {
      value = ($input.aprendiz_horas_praticas_semanais != null ? $input.aprendiz_horas_praticas_semanais : $contrato_atual.aprendiz_horas_praticas_semanais)
    }

    var $aprendiz_teoricas_final {
      value = ($input.aprendiz_horas_teoricas_semanais != null ? $input.aprendiz_horas_teoricas_semanais : $contrato_atual.aprendiz_horas_teoricas_semanais)
    }

    var $aprendiz_jornada_maxima_final {
      value = ($input.aprendiz_jornada_maxima_semanal != null ? $input.aprendiz_jornada_maxima_semanal : $contrato_atual.aprendiz_jornada_maxima_semanal)
    }

    var $temporario_empresa_final {
      value = ($input.temporario_empresa != null ? $input.temporario_empresa : $contrato_atual.temporario_empresa)
    }

    var $temporario_tomadora_final {
      value = ($input.temporario_tomadora != null ? $input.temporario_tomadora : $contrato_atual.temporario_tomadora)
    }

    var $temporario_motivo_final {
      value = ($input.temporario_motivo != null ? $input.temporario_motivo : $contrato_atual.temporario_motivo)
    }

    var $temporario_prazo_final {
      value = ($input.temporario_data_prazo != null ? $input.temporario_data_prazo : $contrato_atual.temporario_data_prazo)
    }

    var $temporario_prorrogacoes_final {
      value = ($input.temporario_prorrogacoes != null ? $input.temporario_prorrogacoes : $contrato_atual.temporario_prorrogacoes)
    }

    var $pj_contrato_numero_final {
      value = ($input.pj_contrato_numero != null ? $input.pj_contrato_numero : $contrato_atual.pj_contrato_numero)
    }

    var $pj_entregas_final {
      value = ($input.pj_entregas != null ? $input.pj_entregas : $contrato_atual.pj_entregas)
    }

    var $pj_vigencia_inicio_final {
      value = ($input.pj_vigencia_inicio != null ? $input.pj_vigencia_inicio : $contrato_atual.pj_vigencia_inicio)
    }

    var $pj_vigencia_fim_final {
      value = ($input.pj_vigencia_fim != null ? $input.pj_vigencia_fim : $contrato_atual.pj_vigencia_fim)
    }

    var $pj_condicoes_final {
      value = ($input.pj_condicoes_comerciais != null ? $input.pj_condicoes_comerciais : $contrato_atual.pj_condicoes_comerciais)
    }

    db.edit contrato_especifico {
      field_name = "id"
      field_value = $contrato_atual.id
      data = {
        estagio_instituicao_ensino       : $estagio_instituicao_final
        estagio_curso                     : $estagio_curso_final
        estagio_termo_compromisso_valido   : $estagio_termo_valido_final
        estagio_termo_compromisso_data      : $estagio_termo_data_final
        estagio_jornada_semanal_maxima       : $estagio_jornada_final
        estagio_recesso_dias_disponivel       : $estagio_recesso_final
        aprendiz_programa                      : $aprendiz_programa_final
        aprendiz_horas_praticas_semanais         : $aprendiz_praticas_final
        aprendiz_horas_teoricas_semanais           : $aprendiz_teoricas_final
        aprendiz_jornada_maxima_semanal              : $aprendiz_jornada_maxima_final
        temporario_empresa                             : $temporario_empresa_final
        temporario_tomadora                              : $temporario_tomadora_final
        temporario_motivo                                  : $temporario_motivo_final
        temporario_data_prazo                                : $temporario_prazo_final
        temporario_prorrogacoes                                : $temporario_prorrogacoes_final
        pj_contrato_numero                                       : $pj_contrato_numero_final
        pj_entregas                                                : $pj_entregas_final
        pj_vigencia_inicio                                           : $pj_vigencia_inicio_final
        pj_vigencia_fim                                                : $pj_vigencia_fim_final
        pj_condicoes_comerciais                                          : $pj_condicoes_final
        updated_at                                                         : "now"
      }
    } as $contrato_atualizado
  }

  response = {
    sucesso  : true
    mensagem : "Contrato especifico atualizado com sucesso."
    contrato : $contrato_atualizado
  }

  guid = "conectahr-contratos-especificos-id-patch-0001"
}
