// Consulta uma avaliacao com suas respostas. Acesso: o avaliador
// designado (sempre), o colaborador avaliado (somente apos enviada,
// para nao expor rascunho), ou RH/ADMIN (sempre).
query "avaliacoes/{id}" verb=GET {
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

    db.get avaliacao {
      field_name = "id"
      field_value = $input.id
    } as $avaliacao_atual

    precondition ($avaliacao_atual != null) {
      error_type = "notfound"
      error = "Avaliacao nao encontrada."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_avaliador {
      value = ($avaliacao_atual.user_id == $usuario_autenticado.id)
    }

    db.get colaborador {
      field_name = "id"
      field_value = $avaliacao_atual.colaborador_id
    } as $colaborador_avaliado

    var $e_o_avaliado {
      value = ($colaborador_avaliado != null && $colaborador_avaliado.user_id == $usuario_autenticado.id)
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_avaliador || ($e_o_avaliado && $avaliacao_atual.status == "enviada")) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar esta avaliacao."
    }

    db.query resposta_avaliacao {
      where = $db.resposta_avaliacao.avaliacao_id == $avaliacao_atual.id
      return = {type: "list"}
    } as $respostas
  }

  response = {
    sucesso   : true
    avaliacao : $avaliacao_atual
    respostas : $respostas
  }

  guid = "conectahr-avaliacoes-id-get-0001"
}
