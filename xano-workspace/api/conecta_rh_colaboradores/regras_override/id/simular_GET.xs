// Simula o impacto de um regra_override (rascunho ou pendente) antes
// da publicacao (item 4.15 e spec.md - "Simulacao antes da
// publicacao"): lista os colaboradores afetados pela abrangencia do
// override e, para cada um, o valor atualmente resolvido do parametro
// versus o valor proposto — sem alterar nenhuma regra vigente nem
// gravar regra_aplicada. Operacao de RH/ADMIN.
query "regras_override/{id}/simular" verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem simular o impacto de uma regra."
    }

    db.get regra_override {
      field_name = "id"
      field_value = $input.id
    } as $override_simulado

    precondition ($override_simulado != null) {
      error_type = "notfound"
      error = "Regra de override nao encontrada."
    }

    // Levanta os colaboradores afetados pela abrangencia do override,
    // um caso por vez. "categoria_profissional" nunca resolve populacao
    // — mesmo gap documentado no resolver_regra (colaborador nao tem
    // esse campo). "estabelecimento" tratado como empresa inteira.
    var $colaboradores_afetados {
      value = []
    }

    conditional {
      if ($override_simulado.abrangencia == "empresa" || $override_simulado.abrangencia == "estabelecimento") {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo"
          return = {type: "list"}
        } as $populacao_empresa

        var.update $colaboradores_afetados {
          value = $populacao_empresa
        }
      }
    }

    conditional {
      if ($override_simulado.abrangencia == "estado" && $override_simulado.estado != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.estado == $override_simulado.estado
          return = {type: "list"}
        } as $populacao_estado

        var.update $colaboradores_afetados {
          value = $populacao_estado
        }
      }
    }

    conditional {
      if ($override_simulado.abrangencia == "municipio" && $override_simulado.municipio != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.cidade == $override_simulado.municipio
          return = {type: "list"}
        } as $populacao_municipio

        var.update $colaboradores_afetados {
          value = $populacao_municipio
        }
      }
    }

    conditional {
      if ($override_simulado.abrangencia == "tipo_contrato" && $override_simulado.tipo_contrato != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.tipo_contrato == $override_simulado.tipo_contrato
          return = {type: "list"}
        } as $populacao_tipo_contrato

        var.update $colaboradores_afetados {
          value = $populacao_tipo_contrato
        }
      }
    }

    conditional {
      if ($override_simulado.abrangencia == "departamento" && $override_simulado.departamento_id != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.departamento_id == $override_simulado.departamento_id
          return = {type: "list"}
        } as $populacao_departamento

        var.update $colaboradores_afetados {
          value = $populacao_departamento
        }
      }
    }

    conditional {
      if ($override_simulado.abrangencia == "cargo" && $override_simulado.cargo_id != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.cargo_id == $override_simulado.cargo_id
          return = {type: "list"}
        } as $populacao_cargo

        var.update $colaboradores_afetados {
          value = $populacao_cargo
        }
      }
    }

    conditional {
      if ($override_simulado.abrangencia == "colaborador" && $override_simulado.colaborador_id != null) {
        db.query colaborador {
          where = $db.colaborador.status == "Ativo" && $db.colaborador.id == $override_simulado.colaborador_id
          return = {type: "list"}
        } as $populacao_individual

        var.update $colaboradores_afetados {
          value = $populacao_individual
        }
      }
    }

    var $total_afetados {
      value = ($colaboradores_afetados|count)
    }

    // Para cada colaborador afetado, resolve o valor atual (antes desta
    // simulacao) do mesmo parametro, para comparar com o valor proposto.
    var $detalhes_simulacao {
      value = []
    }

    foreach ($colaboradores_afetados) {
      each as $colaborador_afetado {
        function.run "ConectaHR/resolver_regra" {
          input = {colaborador_id: $colaborador_afetado.id, parametro: $override_simulado.parametro}
        } as $resolucao_atual

        var $valor_atual_resolvido {
          value = ($resolucao_atual.override_aplicado != null ? $resolucao_atual.override_aplicado.valor_novo : null)
        }

        var $representa_mudanca {
          value = ($valor_atual_resolvido != $override_simulado.valor_novo)
        }

        var.update $detalhes_simulacao {
          value = $detalhes_simulacao|push:{
            colaborador_id    : $colaborador_afetado.id
            nome              : $colaborador_afetado.nome
            valor_atual       : $valor_atual_resolvido
            nivel_atual       : $resolucao_atual.nivel_resolvido
            valor_proposto    : $override_simulado.valor_novo
            representa_mudanca: $representa_mudanca
            conflito_atual    : $resolucao_atual.conflito
          }
        }
      }
    }

    // Auditoria: simulacao executada (nao altera nenhuma regra vigente).
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "simular_impacto_regra_override"
        recurso    : "regra_override"
        registro_id: $override_simulado.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso           : true
    override_simulado : $override_simulado
    total_afetados    : $total_afetados
    detalhes          : $detalhes_simulacao
  }

  guid = "conectahr-regras-override-simular-get-0001"
}
