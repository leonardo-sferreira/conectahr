// DESATIVADO em 12/10/2026 (change ponto-rep-p-e-ferias-clt). O ajuste direto por campo
// gravava o horario direto no registro do dia, sem passar pela ARP do REP-P, o que a Portaria
// MTP 671/2021 nao permite (a marcacao original nao muda; a correcao e um tratamento, art. 82).
// Agora so recusa e indica o endpoint novo:
//   folha_ponto/tratar (inclusao ou desconsideracao, como tratamento).
// Mantido para quem ainda chama o caminho antigo receber uma mensagem clara, em vez de 404.
query "folha_ponto/ajustar" verb=POST {
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
      error = "Este ajuste foi substituido. Atualize a pagina e use Folha de ponto > Ajustar o dia (folha_ponto/tratar)."
    }
  }

  response = {sucesso: false}

  guid = "conectahr-folha-ponto-ajustar-post-0001"
}
