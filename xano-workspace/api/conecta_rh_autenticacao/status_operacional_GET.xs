// Monitoramento operacional (item 7.9). Exclusivo de RH/ADMIN. Reporta
// o estado da fila de e-mail, tarefas manuais pendentes (substitutas das
// rotinas automaticas que este plano Xano nao suporta — ver
// conectahr_xano_platform_quirks, achado 6) e contas atualmente
// bloqueadas por tentativas invalidas de senha.
//
// Backups e recuperacao (tambem previstos no item 7.9) sao
// responsabilidade de infraestrutura do proprio Xano (backups do banco
// gerenciados pela plataforma/plano de hospedagem), fora do alcance de
// codigo XanoScript da aplicacao — documentado em docs/monitoramento.md,
// nao implementado aqui.
query status_operacional verb=GET {
  api_group = "ConectaRH — Autenticação"
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar o status operacional."
    }

    // ---------- Fila de e-mail (email_outbox) ----------
    db.query email_outbox {
      where = $db.email_outbox.status == "pendente"
      return = {type: "count"}
    } as $fila_email_pendente

    db.query email_outbox {
      where = $db.email_outbox.status == "falhou"
      return = {type: "count"}
    } as $fila_email_falhou

    db.query email_outbox {
      where = $db.email_outbox.status == "enviado"
      return = {type: "count"}
    } as $fila_email_enviado

    // ---------- Falhas de tarefas manuais (sem Background Tasks neste plano) ----------
    // Desligamentos agendados cuja data efetiva ja passou e ainda nao
    // foram concluidos manualmente (solicitacoes_desligamento/{id}/concluir).
    var $agora_ts_status_op {
      value = (now|format_timestamp:"Y-m-d":"UTC")
    }

    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.status == "agendado" && $db.solicitacao_desligamento.data_efetiva != null && $db.solicitacao_desligamento.data_efetiva <= $agora_ts_status_op
      return = {type: "count"}
    } as $desligamentos_vencidos_nao_concluidos

    // Documentos aprovados com validade ja vencida que ainda nao foram
    // reprocessados (documentos/processar_vencimentos).
    db.query documento {
      where = $db.documento.status == "aprovado" && $db.documento.data_validade != null && $db.documento.data_validade <= $agora_ts_status_op
      return = {type: "count"}
    } as $documentos_vencidos_nao_processados

    // ---------- Acesso bloqueado ----------
    db.query user {
      where = $db.user.senha_bloqueada_ate != null && $db.user.senha_bloqueada_ate > now
      return = {type: "count"}
    } as $contas_bloqueadas_por_senha
  }

  response = {
    sucesso : true
    fila_email: {pendente: $fila_email_pendente, falhou: $fila_email_falhou, enviado: $fila_email_enviado}
    tarefas_manuais_pendentes: {
      desligamentos_vencidos_nao_concluidos  : $desligamentos_vencidos_nao_concluidos
      documentos_vencidos_nao_processados    : $documentos_vencidos_nao_processados
    }
    acesso_bloqueado: {contas_bloqueadas_por_senha: $contas_bloqueadas_por_senha}
  }

  guid = "conectahr-status-operacional-get-0001"
}
