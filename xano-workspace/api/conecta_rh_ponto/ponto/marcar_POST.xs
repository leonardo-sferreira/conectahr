// Marca o ponto do colaborador autenticado no REP-P (Portaria MTP 671/2021, change
// ponto-rep-p-e-ferias-clt). Grava a marcacao na ARP (marcacao_ponto, registro tipo 7, com NSR
// e hash encadeado), recalcula o dia (registro_ponto, cache) e devolve os dados do comprovante
// de registro de ponto (art. 79). Sem restricao de horario nem de quantidade de marcacoes
// (art. 74): so recusa quem nao tem ficha, nao esta ativo, tem a admissao CLT com eSocial ou
// CTPS pendentes, marca antes da data de admissao ou quando o empregador nao foi cadastrado.
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

    // Bloqueia contas inativas.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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

    // Bloqueia inicio operacional de admissao CLT sem eSocial/CTPS
    // confirmados (item 3.5). So se aplica quando ha um registro de
    // admissao CLT rastreado; nao bloqueia colaboradores anteriores a
    // esse rastreio (esocial_status/ctps_status nulos).
    conditional {
      if ($colaborador_autenticado.tipo_contrato == "CLT") {
        db.query historico_profissional {
          where = $db.historico_profissional.colaborador_id == $colaborador_autenticado.id && $db.historico_profissional.tipo_alteracao == "admissao"
          return = {type: "single"}
        } as $admissao_clt

        var $esocial_pendente {
          value = ($admissao_clt != null && $admissao_clt.esocial_status != null && $admissao_clt.esocial_status != "confirmado")
        }

        var $ctps_pendente {
          value = ($admissao_clt != null && $admissao_clt.ctps_status != null && $admissao_clt.ctps_status != "confirmado")
        }

        precondition ($esocial_pendente == false && $ctps_pendente == false) {
          error_type = "accessdenied"
          error = "Registro eSocial ou anotacao na CTPS Digital da admissao ainda nao confirmados. Contate o RH."
        }
      }
    }

    // Empregador cadastrado: sem ele nao ha comprovante nem AFD validos.
    db.query empregador {
      sort = {empregador.id: "asc"}
      return = {type: "single"}
    } as $empregador

    precondition ($empregador != null) {
      error_type = "accessdenied"
      error = "O ponto ainda nao esta liberado: o RH precisa cadastrar os dados do empregador em Ponto eletronico (REP-P)."
    }

    // Antes da admissao a pessoa ainda nao e empregada: nao ha marcacao.
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $admissao {
      value = ($colaborador_autenticado.data_admissao != null ? ($colaborador_autenticado.data_admissao|format_timestamp:"Y-m-d":"UTC") : null)
    }

    precondition ($admissao == null || $hoje >= $admissao) {
      error_type = "accessdenied"
      error = "Sua admissao e em " ~ ($colaborador_autenticado.data_admissao|format_timestamp:"d/m/Y":"UTC") ~ ". O ponto pode ser marcado a partir dessa data."
    }

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $colaborador_autenticado.cpf}
    } as $cpf

    // Grava a marcacao na ARP (registro tipo 7).
    function.run "ConectaHR/gravar_registro_rep" {
      input = {tipo_registro: 7, colaborador_id: $colaborador_autenticado.id, cpf: $cpf}
    } as $marcacao

    // Recalcula o dia a partir de todas as marcacoes e tratamentos.
    function.run "ConectaHR/atualizar_dia_ponto" {
      input = {colaborador_id: $colaborador_autenticado.id, data: $hoje}
    } as $dia

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "marcar_ponto"
        recurso    : "marcacao_ponto"
        registro_id: $marcacao.id
        valor_novo : "nsr=" ~ ($marcacao.nsr|to_text) ~ "; marcacao_do_dia=" ~ ($dia.quantidade|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso : true
    mensagem: "Ponto marcado."
    registro: $dia.registro
    marcacao: {id: $marcacao.id, nsr: $marcacao.nsr, data_hora_marcacao: $marcacao.data_hora_marcacao, data_hora_marcacao_txt: $marcacao.data_hora_marcacao_txt, hash: $marcacao.hash, ordem_no_dia: $dia.quantidade}
    comprovante: {
      empregador: {razao_social: $empregador.razao_social, tipo_identificador: $empregador.tipo_identificador, identificador: $empregador.identificador, cno_caepf: $empregador.cno_caepf, local_prestacao: $empregador.local_prestacao, inpi_registro: $empregador.inpi_registro}
      trabalhador: {nome: $colaborador_autenticado.nome, cpf: $cpf}
    }
  }

  guid = "conectahr-ponto-marcar-0001"
}
