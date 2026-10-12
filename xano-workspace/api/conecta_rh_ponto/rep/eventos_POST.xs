// Registra a indisponibilidade (08) ou a volta da disponibilidade (07) do servico de ponto
// (Portaria MTP 671/2021, AFD registro tipo 6). Somente RH ou Admin. Auditado.
query "rep/eventos" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    enum evento {
      values = ["07", "08"]
    }

    text? observacao? filters=trim|max:200
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
      error = "Somente RH ou Admin podem registrar eventos do ponto."
    }

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $ficha_responsavel

    var $cpf_responsavel {
      value = ($ficha_responsavel != null && $ficha_responsavel.cpf != null ? $ficha_responsavel.cpf : "")
    }

    function.run "ConectaHR/somente_digitos" {
      input = {texto: $cpf_responsavel}
    } as $cpf_responsavel_digitos

    function.run "ConectaHR/gravar_registro_rep" {
      input = {tipo_registro: 6, cpf_responsavel: $cpf_responsavel_digitos, responsavel_user_id: $usuario_autenticado.id, dados: {evento: $input.evento, observacao: $input.observacao}}
    } as $registro_rep

    db.query empregador {
      sort = {empregador.id: "asc"}
      return = {type: "single"}
    } as $empregador

    conditional {
      if ($empregador != null) {
        db.edit empregador {
          field_name = "id"
          field_value = $empregador.id
          data = {servico_disponivel: ($input.evento == "07"), updated_at: "now"}
        } as $empregador_editado
      }
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : ($input.evento == "07" ? "rep_servico_disponivel" : "rep_servico_indisponivel")
        recurso    : "marcacao_ponto"
        registro_id: $registro_rep.id
        valor_novo : "nsr=" ~ ($registro_rep.nsr|to_text) ~ "; evento=" ~ $input.evento
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {sucesso: true, nsr: $registro_rep.nsr, evento: $input.evento}

  guid = "conectahr-rep-eventos-post-0001"
}
