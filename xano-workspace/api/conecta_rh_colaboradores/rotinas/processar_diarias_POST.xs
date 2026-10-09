// Rotina diaria de acionamento manual (RH e Admin): aplica as transicoes de
// status que dependem da data. O plano do Xano deste projeto nao tem tarefas
// agendadas, entao quem aciona e uma pessoa. Idempotente: uma segunda execucao
// seguida devolve contagens zeradas. Ver `ConectaHR/processar_transicoes_diarias`.
query "rotinas/processar_diarias" verb=POST {
  api_group = "ConectaRH — Colaboradores"
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem acionar a rotina diaria."
    }

    function.run "ConectaHR/processar_transicoes_diarias" {
      input = {aplicar: true, usuario_id: $usuario_autenticado.id}
    } as $contagens

    db.add auditoria {
      data = {
        user_id      : $usuario_autenticado.id
        acao         : "processar_rotinas_diarias"
        recurso      : "rotina"
        justificativa: ("desligamentos=" ~ ($contagens.desligamentos_concluidos|to_text) ~ "; ferias_concluidas=" ~ ($contagens.ferias_concluidas|to_text) ~ "; ponto_incompleto=" ~ ($contagens.ponto_para_incompleto|to_text) ~ "; instrumentos_expirados=" ~ ($contagens.instrumentos_expirados|to_text) ~ "; para_ferias=" ~ ($contagens.colaboradores_para_ferias|to_text) ~ "; para_afastado=" ~ ($contagens.colaboradores_para_afastado|to_text) ~ "; para_ativo=" ~ ($contagens.colaboradores_para_ativo|to_text))
        resultado    : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso  : true
    mensagem : "Rotina diaria processada."
    aplicadas: $contagens
  }

  guid = "conectahr-rotinas-processar-diarias-post-0001"
}
