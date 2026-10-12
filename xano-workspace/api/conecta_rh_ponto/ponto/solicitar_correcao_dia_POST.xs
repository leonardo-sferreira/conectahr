// DESATIVADO em 12/10/2026 (change ponto-rep-p-e-ferias-clt). O pedido de correcao de dia sem marcacao
// gravava o horario direto no registro do dia, sem passar pela ARP do REP-P, o que a Portaria
// MTP 671/2021 nao permite (a marcacao original nao muda; a correcao e um tratamento, art. 82).
// Agora so recusa e indica o endpoint novo:
//   ponto/correcao (inclusao de uma marcacao).
// Mantido para quem ainda chama o caminho antigo receber uma mensagem clara, em vez de 404.
query "ponto/solicitar_correcao_dia" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
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

    precondition (false) {
      error_type = "inputerror"
      error = "Este pedido de correcao foi substituido. Atualize a pagina e use Ponto > Mes > Pedir correcao do dia (ponto/correcao)."
    }
  }

  response = {sucesso: false}

  guid = "conectahr-ponto-solicitar-correcao-dia-post-0001"
}
