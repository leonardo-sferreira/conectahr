// Atualiza o vinculo profissional de um colaborador.
// Operacao exclusiva de uma conta RH ativa.
// Atualiza cargo, departamento, contrato, nivel, salario e carga horaria.
// Encerra o historico anterior e cria um novo registro.
query "colaboradores/{id}/vinculo" verb=PATCH {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
    int cargo_id
    int departamento_id
    text tipo_contrato filters=trim
    text nivel filters=trim
    decimal salario filters=min:0
    decimal carga_horaria_semanal filters=min:1|max:60
    date data_inicio
    text tipo_alteracao filters=trim
    text motivo_alteracao filters=trim|min:3|max:1000
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_rh
  
    precondition ($usuario_rh != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }
  
    // Bloqueia contas inativas.
    precondition ($usuario_rh.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_rh.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_rh {
      value = $usuario_rh.perfil|trim|to_upper
    }
  
    // Somente RH pode atualizar vinculos profissionais.
    precondition ($perfil_rh == "RH") {
      error_type = "accessdenied"
      error = "Somente o RH pode atualizar vinculos profissionais."
    }
  
    // Localiza o colaborador.
    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_atual
  
    precondition ($colaborador_atual != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }
  
    // Impede alteracao de colaborador desligado.
    var $status_colaborador {
      value = $colaborador_atual.status|trim|to_upper
    }
  
    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel alterar o vinculo de um colaborador desligado."
    }
  
    // A alteracao nao pode ser anterior a admissao.
    precondition ($input.data_inicio >= $colaborador_atual.data_admissao) {
      error_type = "inputerror"
      error = "A data da alteracao nao pode ser anterior a data de admissao."
    }
  
    // Localiza e valida o cargo.
    db.get cargo {
      field_name = "id"
      field_value = $input.cargo_id
    } as $cargo
  
    precondition ($cargo != null) {
      error_type = "notfound"
      error = "Cargo nao encontrado."
    }
  
    precondition ($cargo.ativo) {
      error_type = "inputerror"
      error = "Nao e possivel vincular um cargo inativo."
    }
  
    // Localiza e valida o departamento.
    db.get departamento {
      field_name = "id"
      field_value = $input.departamento_id
    } as $departamento
  
    precondition ($departamento != null) {
      error_type = "notfound"
      error = "Departamento nao encontrado."
    }
  
    precondition ($departamento.ativo) {
      error_type = "inputerror"
      error = "Nao e possivel vincular um departamento inativo."
    }
  
    // Normaliza o tipo de contrato.
    var $tipo_contrato_normalizado {
      value = $input.tipo_contrato|trim|to_upper
    }
  
    // Valida os tipos de contrato permitidos.
    precondition ($tipo_contrato_normalizado == "CLT" || $tipo_contrato_normalizado == "PJ" || $tipo_contrato_normalizado == "ESTAGIO" || $tipo_contrato_normalizado == "APRENDIZ" || $tipo_contrato_normalizado == "TEMPORARIO" || $tipo_contrato_normalizado == "OUTRO") {
      error_type = "inputerror"
      error = "Tipo de contrato invalido."
    }
  
    // Normaliza o nivel profissional.
    var $nivel_normalizado {
      value = $input.nivel|trim|to_lower
    }
  
    // Valida os niveis configurados no Enum.
    precondition ($nivel_normalizado == "l1" || $nivel_normalizado == "l2" || $nivel_normalizado == "l3" || $nivel_normalizado == "l4" || $nivel_normalizado == "l5") {
      error_type = "inputerror"
      error = "Nivel profissional invalido. Use l1, l2, l3, l4 ou l5."
    }
  
    // Normaliza o tipo de alteracao profissional.
    var $tipo_alteracao_normalizado {
      value = $input.tipo_alteracao|trim|to_lower
    }
  
    // Valida os valores exatos do Enum.
    precondition ($tipo_alteracao_normalizado == "promocao" || $tipo_alteracao_normalizado == "alteracao_departamento" || $tipo_alteracao_normalizado == "alteracao_salarial" || $tipo_alteracao_normalizado == "alteracao_cargo" || $tipo_alteracao_normalizado == "alteracao_contratual") {
      error_type = "inputerror"
      error = "Tipo de alteracao profissional invalido."
    }
  
    // Normaliza o nivel atual para comparacao.
    var $nivel_atual_normalizado {
      value = $colaborador_atual.nivel|trim|to_lower
    }
  
    // Identifica se houve mudanca de nivel.
    var $nivel_mudou {
      value = $nivel_atual_normalizado != $nivel_normalizado
    }
  
    // Preserva nivel_desde quando o nivel nao mudou.
    var $nivel_desde_final {
      value = $colaborador_atual.nivel_desde
    }
  
    // Quando o nivel muda, inicia a contagem na data da alteracao.
    conditional {
      if ($nivel_mudou) {
        var.update $nivel_desde_final {
          value = $input.data_inicio
        }
      }
    }
  
    // Localiza o registro profissional mais recente.
    db.query historico_profissional {
      where = $db.historico_profissional.colaborador_id == $colaborador_atual.id
      sort = {historico_profissional.data_inicio: "desc"}
      return = {type: "single"}
    } as $historico_atual
  
    // Define o tipo que sera gravado no novo historico.
    var $tipo_historico {
      value = $tipo_alteracao_normalizado
    }
  
    // Se ainda nao existir historico, registra como admissao.
    conditional {
      if ($historico_atual == null) {
        var.update $tipo_historico {
          value = "admissao"
        }
      }
    }
  
    // Atualiza o colaborador e o historico como uma unica operacao.
    db.transaction {
      stack {
        // Encerra o historico anterior quando ele estiver aberto.
        conditional {
          if ($historico_atual != null) {
            conditional {
              if ($historico_atual.data_fim == null) {
                db.edit historico_profissional {
                  field_name = "id"
                  field_value = $historico_atual.id
                  data = {data_fim: $input.data_inicio, updated_at: "now"}
                } as $historico_encerrado
              }
            }
          }
        }
      
        // Atualiza o vinculo profissional atual.
        db.edit colaborador {
          field_name = "id"
          field_value = $colaborador_atual.id
          data = {
            cargo_id             : $cargo.id
            departamento_id      : $departamento.id
            tipo_contrato        : $tipo_contrato_normalizado
            nivel                : $nivel_normalizado
            nivel_desde          : $nivel_desde_final
            salario              : $input.salario
            carga_horaria_semanal: $input.carga_horaria_semanal
            updated_at           : "now"
          }
        } as $colaborador_atualizado
      
        // Cria o novo registro de historico profissional.
        db.add historico_profissional {
          data = {
            colaborador_id       : $colaborador_atual.id
            cargo_id             : $cargo.id
            departamento_id      : $departamento.id
            tipo_contrato        : $tipo_contrato_normalizado
            nivel                : $nivel_normalizado
            salario              : $input.salario
            carga_horaria_semanal: $input.carga_horaria_semanal
            data_inicio          : $input.data_inicio
            data_fim             : null
            tipo_alteracao       : $tipo_historico
            motivo_alteracao     : $input.motivo_alteracao
            user_id              : $usuario_rh.id
            updated_at           : "now"
          }
        } as $historico_criado
      }
    }
  }

  response = {
    sucesso    : true
    mensagem   : "Vinculo profissional atualizado e historico registrado com sucesso."
    colaborador: $colaborador_atualizado
    historico  : $historico_criado
    nivel_mudou: $nivel_mudou
  }

  guid = "WDN_0gQ33NfFufs3ax68BXgwjo8"
}