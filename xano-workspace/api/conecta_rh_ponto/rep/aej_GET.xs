// Dados do AEJ (Portaria MTP 671/2021, Anexo VI; leiaute "002" de 31/07/2026) do periodo:
// marcacoes (tipo 7), tratamentos, faltas nao justificadas, banco de horas e os vinculos que
// tiveram algum desses registros. O frontend monta o arquivo (frontend/rep_modelo.gerar_aej).
// Somente RH ou Admin. Auditado.
query "rep/aej" verb=GET {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    date data_inicio
    date data_fim
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

    // Sessao do token: precisa existir, ser do usuario, estar ativa e no prazo.
    db.get sessao {
      field_name = "id"
      field_value = $auth.extras.sessao_id
    } as $sessao_token

    precondition ($sessao_token.ativa) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.user_id == $auth.id) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.revogada_em == null) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($sessao_token.expira_em > now) {
      error_type = "unauthorized"
      error = "Sessao encerrada ou expirada. Faca login novamente."
    }

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem gerar o AEJ."
    }

    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }

    db.query empregador {
      sort = {empregador.id: "asc"}
      return = {type: "single"}
    } as $empregador

    precondition ($empregador != null) {
      error_type = "badrequest"
      error = "Cadastre o empregador antes de gerar os arquivos do ponto."
    }

    db.query marcacao_ponto {
      where = $db.marcacao_ponto.tipo_registro == 7 && $db.marcacao_ponto.data >= $input.data_inicio && $db.marcacao_ponto.data <= $input.data_fim
      sort = {marcacao_ponto.nsr: "asc"}
      return = {type: "list"}
      output = ["id", "colaborador_id", "data", "data_hora_marcacao_txt"]
    } as $marcacoes

    db.query tratamento_ponto {
      where = $db.tratamento_ponto.data >= $input.data_inicio && $db.tratamento_ponto.data <= $input.data_fim
      sort = {tratamento_ponto.id: "asc"}
      return = {type: "list"}
      output = ["id", "colaborador_id", "data", "tipo", "marcacao_id", "data_hora", "motivo", "anula_tratamento_id"]
    } as $tratamentos

    // Falta nao justificada (AEJ registro 07, codigo 2): ausencia do tipo Falta aprovada ou
    // registrada pelo RH. Atestado, licenca e afastamento nao entram.
    db.query ausencia {
      where = $db.ausencia.tipo == "Falta" && ($db.ausencia.status == "Aprovada" || $db.ausencia.status == "Registrado") && $db.ausencia.data_inicio <= $input.data_fim && $db.ausencia.data_fim >= $input.data_inicio
      return = {type: "list"}
      output = ["colaborador_id", "data_inicio", "data_fim"]
    } as $faltas

    db.query banco_horas_lancamento {
      where = $db.banco_horas_lancamento.data_lancamento >= $input.data_inicio && $db.banco_horas_lancamento.data_lancamento <= $input.data_fim
      sort = {banco_horas_lancamento.data_lancamento: "asc"}
      return = {type: "list"}
      output = ["colaborador_id", "data_lancamento", "horas", "tipo"]
    } as $banco_horas

    // Vinculos: so quem tem algum registro no periodo (ids em texto ",9,12,"; o contains em
    // lista nao reconhece o id nas chamadas por HTTP).
    var $ids {
      value = ","
    }

    foreach ($marcacoes) {
      each as $m {
        var.update $ids {
          value = $ids ~ ($m.colaborador_id|to_text) ~ ","
        }
      }
    }

    foreach ($tratamentos) {
      each as $t {
        var.update $ids {
          value = $ids ~ ($t.colaborador_id|to_text) ~ ","
        }
      }
    }

    foreach ($faltas) {
      each as $f {
        var.update $ids {
          value = $ids ~ ($f.colaborador_id|to_text) ~ ","
        }
      }
    }

    foreach ($banco_horas) {
      each as $b {
        var.update $ids {
          value = $ids ~ ($b.colaborador_id|to_text) ~ ","
        }
      }
    }

    db.query colaborador {
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "cpf"]
    } as $colaboradores

    var $vinculos {
      value = []
    }

    foreach ($colaboradores) {
      each as $c {
        conditional {
          if ($ids|contains:("," ~ ($c.id|to_text) ~ ",")) {
            var $vinculo {
              value = {}|set:"colaborador_id":$c.id|set:"nome":$c.nome|set:"cpf":$c.cpf
            }

            var.update $vinculos {
              value = $vinculos|push:$vinculo
            }
          }
        }
      }
    }

    db.add auditoria {
      data = {
        user_id   : $usuario_autenticado.id
        acao      : "rep_aej_gerado"
        recurso   : "marcacao_ponto"
        valor_novo: "periodo=" ~ $input.data_inicio ~ ".." ~ $input.data_fim ~ "; vinculos=" ~ (($vinculos|count)|to_text) ~ "; marcacoes=" ~ (($marcacoes|count)|to_text)
        resultado : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    empregador : $empregador
    vinculos   : $vinculos
    marcacoes  : $marcacoes
    tratamentos: $tratamentos
    faltas     : $faltas
    banco_horas: $banco_horas
  }

  guid = "conectahr-rep-aej-get-0001"
}
