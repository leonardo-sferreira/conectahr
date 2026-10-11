// Vincula uma conta de acesso que ainda nao tem ficha a um cadastro de
// colaborador existente (por exemplo, a conta de RH ou de Admin criada antes
// da ficha). Sem a ficha, a pessoa nao marca ponto nem pede ferias.
// ADMIN vincula qualquer conta; RH so contas de COLABORADOR (mesma regra de
// usuarios/{id} PATCH). Ninguem vincula a propria conta: quem se ligasse a
// ficha de outra pessoa passaria a marcar ponto e pedir ferias como ela.
// A ficha precisa estar sem conta e nao pode ser de colaborador desligado.
// Tarefa 50 da change concluir-frontend-streamlit.
query "usuarios/{id}/vincular_colaborador" verb=POST {
  api_group = "ConectaRH — Gestão de Usuários"
  auth = "user"

  input {
    int id
    int colaborador_id
  }

  stack {
    // Localiza o usuário autenticado.
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $usuario_autenticado

    precondition ($usuario_autenticado != null) {
      error_type = "unauthorized"
      error = "Usuário autenticado não encontrado."
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

    // Impede o uso por uma conta inativa.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "ADMIN" || $perfil_autenticado == "RH") {
      error_type = "accessdenied"
      error = "Somente Admin ou RH podem vincular contas a colaboradores."
    }

    // Ninguem vincula a propria conta.
    precondition ($input.id != $usuario_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao pode vincular a propria conta. Peca a outra pessoa do RH ou do Admin."
    }

    db.get user {
      field_name = "id"
      field_value = $input.id
    } as $usuario_alvo

    precondition ($usuario_alvo != null) {
      error_type = "notfound"
      error = "Usuário não encontrado."
    }

    var $perfil_alvo {
      value = $usuario_alvo.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "ADMIN" || $perfil_alvo == "COLABORADOR") {
      error_type = "accessdenied"
      error = "O RH pode vincular somente contas de colaboradores."
    }

    // A conta ainda nao pode ter ficha.
    db.query colaborador {
      where = $db.colaborador.user_id == $usuario_alvo.id
      return = {type: "single"}
    } as $ficha_atual

    precondition ($ficha_atual == null) {
      error_type = "inputerror"
      error = "Esta conta ja esta vinculada a um colaborador."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador

    precondition ($colaborador != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    precondition ($colaborador.user_id == null) {
      error_type = "inputerror"
      error = "Este colaborador ja possui uma conta de acesso."
    }

    var $status_colaborador {
      value = $colaborador.status|trim|to_upper
    }

    precondition ($status_colaborador != "DESLIGADO") {
      error_type = "inputerror"
      error = "Nao e possivel vincular a conta a um colaborador desligado."
    }

    db.edit colaborador {
      field_name = "id"
      field_value = $colaborador.id
      data = {user_id: $usuario_alvo.id, updated_at: "now"}
    } as $colaborador_vinculado

    // Auditoria: vinculo de conta a ficha (ids apenas, sem dados pessoais).
    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "vincular_conta_colaborador"
        recurso    : "user"
        registro_id: $usuario_alvo.id
        valor_novo : "colaborador_id=" ~ ($colaborador.id|to_text)
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso       : true
    mensagem      : "Conta vinculada ao colaborador. A pessoa ja pode marcar ponto e pedir ferias."
    usuario_id    : $usuario_alvo.id
    colaborador_id: $colaborador_vinculado.id
  }

  guid = "conectahr-usuarios-vincular-colaborador-post-0001"
}
