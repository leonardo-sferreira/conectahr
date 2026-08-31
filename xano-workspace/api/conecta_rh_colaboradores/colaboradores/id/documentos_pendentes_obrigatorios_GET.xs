// Verifica, para um colaborador, quais documentos obrigatorios da
// matriz (item 5.8) ele ainda nao tem aprovados. Casa regras por
// tipo_contrato/cargo/departamento/idade (calculada a partir de
// data_nascimento); regras com nacionalidade/condicao_profissional
// preenchidas sao incluidas com `aplicabilidade_incerta: true`, pois
// colaborador nao tem esses campos para confirmar (mesmo gap
// documentado em resolver_regra.xs). Acesso: RH/ADMIN ou o proprio
// colaborador.
query "colaboradores/{id}/documentos_pendentes_obrigatorios" verb=GET {
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

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo != null && $colaborador_alvo.user_id == $usuario_autenticado.id)
    }

    // Autorizacao checada antes de qualquer estado do colaborador.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar as pendencias documentais deste colaborador."
    }

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    // Idade aproximada em anos (divisor inteiro 365 em vez de 365.25 —
    // aritmetica com literal fracionario nao tem precedente testado
    // neste workspace; a imprecisao de ate 1 dia por ano nao afeta
    // comparacoes de idade minima/maxima em anos inteiros). data_nascimento
    // e um campo "date" (string) — precisa de |to_timestamp antes de
    // aritmetica, e o valor precisa estar pre-extraido antes de combinar
    // com now (ver conectahr-xano-platform-quirks, achado 13).
    var $idade_colaborador {
      value = null
    }

    conditional {
      if ($colaborador_alvo.data_nascimento != null) {
        var $data_nascimento_ts {
          value = ($colaborador_alvo.data_nascimento|to_timestamp)
        }

        var $agora_idade {
          value = now
        }

        var.update $idade_colaborador {
          value = (((($agora_idade - $data_nascimento_ts) / 86400000) / 365)|to_int)
        }
      }
    }

    db.query documento_obrigatorio_regra {
      where = $db.documento_obrigatorio_regra.ativo == true
      return = {type: "list"}
    } as $regras_ativas

    var $pendencias {
      value = []
    }

    var $total_aplicaveis {
      value = 0
    }

    foreach ($regras_ativas) {
      each as $regra_item {
        var $aplica_contrato {
          value = ($regra_item.tipo_contrato == null || $regra_item.tipo_contrato == $colaborador_alvo.tipo_contrato)
        }

        var $aplica_cargo {
          value = ($regra_item.cargo_id == null || $regra_item.cargo_id == $colaborador_alvo.cargo_id)
        }

        var $aplica_departamento {
          value = ($regra_item.departamento_id == null || $regra_item.departamento_id == $colaborador_alvo.departamento_id)
        }

        var $aplica_idade_minima {
          value = ($regra_item.idade_minima == null || ($idade_colaborador != null && $idade_colaborador >= $regra_item.idade_minima))
        }

        var $aplica_idade_maxima {
          value = ($regra_item.idade_maxima == null || ($idade_colaborador != null && $idade_colaborador <= $regra_item.idade_maxima))
        }

        var $aplicabilidade_incerta_item {
          value = ($regra_item.nacionalidade != null || $regra_item.condicao_profissional != null)
        }

        conditional {
          if ($regra_item.obrigatorio == true && $aplica_contrato && $aplica_cargo && $aplica_departamento && $aplica_idade_minima && $aplica_idade_maxima) {
            var.update $total_aplicaveis {
              value = $total_aplicaveis + 1
            }

            db.query documento {
              where = $db.documento.colaborador_id == $colaborador_alvo.id && $db.documento.tipo == $regra_item.tipo_documento && $db.documento.status == "aprovado"
              return = {type: "single"}
            } as $documento_existente

            conditional {
              if ($documento_existente == null) {
                var.update $pendencias {
                  value = $pendencias|push:{
                    regra_id             : $regra_item.id
                    tipo_documento       : $regra_item.tipo_documento
                    exige_frente_verso   : $regra_item.exige_frente_verso
                    prazo_dias_para_envio: $regra_item.prazo_dias_para_envio
                    aplicabilidade_incerta: $aplicabilidade_incerta_item
                  }
                }
              }
            }
          }
        }
      }
    }

    var $total_pendencias {
      value = ($pendencias|count)
    }
  }

  response = {
    sucesso           : true
    colaborador_id     : $colaborador_alvo.id
    total_aplicaveis   : $total_aplicaveis
    total_pendencias   : $total_pendencias
    pendencias         : $pendencias
  }

  guid = "conectahr-colaboradores-documentos-pendentes-obrigatorios-get-0001"
}
