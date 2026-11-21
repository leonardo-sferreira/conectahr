// Registros do AFD (Portaria MTP 671/2021, Anexo V; leiaute "004" de 31/07/2026) gravados no
// periodo: tipos 2, 5, 6 e 7 do ARP em ordem de NSR, com os dados do empregador e do REP-P. O
// frontend monta o arquivo (frontend/rep_modelo.gerar_afd). Somente RH ou Admin. Auditado.
query "rep/afd" verb=GET {
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
      error = "Somente RH ou Admin podem gerar o AFD."
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

    // Periodo pela data e hora de gravacao no horario de Brasilia, dias inteiros.
    var $de {
      value = $input.data_inicio ~ "T00:00:00-0300"
    }

    var $ate {
      value = $input.data_fim ~ "T23:59:59-0300"
    }

    db.query marcacao_ponto {
      where = $db.marcacao_ponto.data_hora_gravacao >= $de && $db.marcacao_ponto.data_hora_gravacao <= $ate
      sort = {marcacao_ponto.nsr: "asc"}
      return = {type: "list"}
      output = ["nsr", "tipo_registro", "cpf", "data_hora_marcacao_txt", "data_hora_gravacao_txt", "coletor", "offline", "hash", "hash_anterior", "cpf_responsavel", "dados"]
    } as $registros

    db.add auditoria {
      data = {
        user_id   : $usuario_autenticado.id
        acao      : "rep_afd_gerado"
        recurso   : "marcacao_ponto"
        valor_novo: "periodo=" ~ $input.data_inicio ~ ".." ~ $input.data_fim ~ "; registros=" ~ (($registros|count)|to_text)
        resultado : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {empregador: $empregador, registros: $registros}

  guid = "conectahr-rep-afd-get-0001"
}
