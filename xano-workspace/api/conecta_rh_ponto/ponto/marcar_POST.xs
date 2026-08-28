// Registra o proximo marcador de ponto do dia para o colaborador autenticado.
// Ordem: entrada -> inicio do intervalo -> fim do intervalo -> saida.
// Cria o registro do dia na primeira marcacao (entrada) e calcula as
// horas trabalhadas quando a saida e registrada.
query "ponto/marcar" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
  }

  stack {
    // Localiza o usuario autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuario autenticado nao encontrado."
    }

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    // Localiza o colaborador vinculado a conta autenticada.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }

    // Somente colaborador profissionalmente ativo pode registrar ponto.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }

    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem registrar ponto."
    }

    // Data de hoje, usada para localizar ou criar o registro do dia.
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"UTC"
    }

    // Localiza o registro de ponto do dia, se existir.
    db.query registro_ponto {
      where = $db.registro_ponto.colaborador_id == $colaborador_autenticado.id && $db.registro_ponto.data == $hoje
      return = {type: "single"}
    } as $registro_hoje

    // Guarda o id do registro final, definido em um dos ramos abaixo.
    var $registro_ponto_id {
      value = 0
    }

    // Ramo 1: primeira marcacao do dia, registra a entrada.
    conditional {
      if ($registro_hoje == null) {
        db.add registro_ponto {
          data = {
            colaborador_id: $colaborador_autenticado.id
            data          : $hoje
            hora_entrada  : now
            status        : "Aberto"
            updated_at    : "now"
          }
        } as $registro_criado

        var.update $registro_ponto_id {
          value = $registro_criado.id
        }
      }
    }

    // Ramo 2: segunda marcacao, inicio do intervalo.
    conditional {
      if ($registro_hoje != null && $registro_hoje.inicio_intervalo == null) {
        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_hoje.id
          data = {inicio_intervalo: now, updated_at: "now"}
        } as $registro_intervalo_iniciado

        var.update $registro_ponto_id {
          value = $registro_intervalo_iniciado.id
        }
      }
    }

    // Ramo 3: terceira marcacao, fim do intervalo.
    conditional {
      if ($registro_hoje != null && $registro_hoje.inicio_intervalo != null && $registro_hoje.fim_intervalo == null) {
        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_hoje.id
          data = {fim_intervalo: now, updated_at: "now"}
        } as $registro_intervalo_finalizado

        var.update $registro_ponto_id {
          value = $registro_intervalo_finalizado.id
        }
      }
    }

    // Ramo 4: quarta marcacao, saida. Calcula as horas trabalhadas.
    conditional {
      if ($registro_hoje != null && $registro_hoje.fim_intervalo != null && $registro_hoje.hora_saida == null) {
        var $duracao_bruta_ms {
          value = now - $registro_hoje.hora_entrada
        }

        var $duracao_intervalo_ms {
          value = $registro_hoje.fim_intervalo - $registro_hoje.inicio_intervalo
        }

        var $duracao_trabalhada_ms {
          value = $duracao_bruta_ms - $duracao_intervalo_ms
        }

        var $horas_trabalhadas_calculadas {
          value = $duracao_trabalhada_ms / 3600000
        }

        db.edit registro_ponto {
          field_name = "id"
          field_value = $registro_hoje.id
          data = {
            hora_saida       : now
            horas_trabalhadas: $horas_trabalhadas_calculadas
            status           : "Completo"
            updated_at       : "now"
          }
        } as $registro_finalizado

        var.update $registro_ponto_id {
          value = $registro_finalizado.id
        }
      }
    }

    // Ramo 5: todos os quatro marcadores do dia ja foram registrados.
    conditional {
      if ($registro_hoje != null && $registro_hoje.hora_saida != null) {
        precondition (false) {
          error_type = "inputerror"
          error = "Todos os marcadores de ponto de hoje ja foram registrados."
        }
      }
    }

    // Recarrega o registro final para a resposta.
    db.get registro_ponto {
      field_name = "id"
      field_value = $registro_ponto_id
    } as $registro_atualizado
  }

  response = {
    sucesso : true
    mensagem: "Marcacao de ponto registrada com sucesso."
    registro: $registro_atualizado
  }

  guid = "conectahr-ponto-marcar-0001"
}
