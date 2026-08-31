// Aprova (ativa como vigente) uma regra_override pendente. Bloqueia
// autoaprovacao. Regras vigentes nao sao sobrescritas: se ja existir
// uma regra vigente com o mesmo parametro, abrangencia e escopo
// (departamento/cargo/colaborador), ela e encerrada (nao editada) e a
// nova versao referencia a versao anterior incrementada - preserva o
// historico completo.
query "regras_override/{id}/aprovar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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
      error = "Somente RH ou ADMIN podem aprovar regras de override."
    }

    db.get regra_override {
      field_name = "id"
      field_value = $input.id
    } as $override_atual

    precondition ($override_atual != null) {
      error_type = "notfound"
      error = "Regra de override nao encontrada."
    }

    precondition ($override_atual.status == "pendente_aprovacao") {
      error_type = "inputerror"
      error = "Somente regras pendentes de aprovacao podem ser aprovadas."
    }

    precondition ($override_atual.criado_por_user_id != $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Quem criou a regra nao pode aprova-la."
    }

    // Localiza uma regra vigente com o mesmo parametro, abrangencia e escopo
    // completo (todas as sete dimensoes de abrangencia, nao so
    // departamento/cargo/colaborador, senao overrides por estado/municipio/
    // tipo_contrato/categoria_profissional encerrariam a regra vigente
    // errada de outra jurisdicao com o mesmo parametro+abrangencia).
    db.query regra_override {
      where = $db.regra_override.parametro == $override_atual.parametro && $db.regra_override.abrangencia == $override_atual.abrangencia && $db.regra_override.status == "vigente" && (($db.regra_override.departamento_id == $override_atual.departamento_id) || ($db.regra_override.departamento_id == null && $override_atual.departamento_id == null)) && (($db.regra_override.cargo_id == $override_atual.cargo_id) || ($db.regra_override.cargo_id == null && $override_atual.cargo_id == null)) && (($db.regra_override.colaborador_id == $override_atual.colaborador_id) || ($db.regra_override.colaborador_id == null && $override_atual.colaborador_id == null)) && (($db.regra_override.tipo_contrato == $override_atual.tipo_contrato) || ($db.regra_override.tipo_contrato == null && $override_atual.tipo_contrato == null)) && (($db.regra_override.estado == $override_atual.estado) || ($db.regra_override.estado == null && $override_atual.estado == null)) && (($db.regra_override.municipio == $override_atual.municipio) || ($db.regra_override.municipio == null && $override_atual.municipio == null)) && (($db.regra_override.categoria_profissional == $override_atual.categoria_profissional) || ($db.regra_override.categoria_profissional == null && $override_atual.categoria_profissional == null))
      return = {type: "single"}
    } as $override_vigente_anterior

    var $versao_final {
      value = 1
    }

    conditional {
      if ($override_vigente_anterior != null) {
        var.update $versao_final {
          value = $override_vigente_anterior.versao + 1
        }
      }
    }

    db.transaction {
      stack {
        conditional {
          if ($override_vigente_anterior != null) {
            db.edit regra_override {
              field_name = "id"
              field_value = $override_vigente_anterior.id
              data = {
                status     : "encerrada"
                ativo      : false
                data_fim   : $override_atual.data_inicio
                updated_at : "now"
              }
            } as $override_encerrado
          }
        }

        db.edit regra_override {
          field_name = "id"
          field_value = $override_atual.id
          data = {
            status                : "vigente"
            ativo                 : true
            versao                : $versao_final
            aprovado_por_user_id  : $usuario_autenticado.id
            data_aprovacao          : "now"
            updated_at                 : "now"
          }
        } as $override_aprovado

        // Auditoria: aprovacao de regra de override.
        db.add auditoria {
          data = {
            user_id       : $usuario_autenticado.id
            acao          : "aprovar_regra_override"
            recurso       : "regra_override"
            registro_id   : $override_atual.id
            valor_anterior: ($override_vigente_anterior != null ? $override_vigente_anterior.valor_novo : null)
            valor_novo    : $override_atual.valor_novo
            resultado     : "sucesso"
          }
        } as $evento_auditoria
      }
    }
  }

  response = {
    sucesso  : true
    mensagem : "Regra de override aprovada e vigente."
    override : $override_aprovado
  }

  guid = "conectahr-regras-override-aprovar-post-0001"
}
