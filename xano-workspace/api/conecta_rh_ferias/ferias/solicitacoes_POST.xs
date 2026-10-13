// Cria uma solicitacao de ferias para o usuario autenticado.
// Permite qualquer perfil com colaborador ativo vinculado.
// Nao recebe colaborador_id ou user_id.
query "ferias/solicitacoes" verb=POST {
  api_group = "ConectaRH — Férias"
  auth = "user"

  input {
    date data_inicio
    date data_fim
    int quantidade_dias filters=min:1|max:30
    // Dias vendidos junto com este periodo (abono pecuniario): 0 a 10 na CLT.
    int? dias_abono? filters=min:0|max:30
    // Observacao opcional para quem decide (Figma 221:230); vai para observacao_colaborador.
    text? observacao? filters=trim|max:500
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
  
    // Contas inativas nao podem solicitar ferias.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Localiza o colaborador pelo token.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado
  
    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a conta autenticada."
    }
  
    // Somente colaborador profissionalmente ativo
    // pode criar uma solicitacao.
    var $status_colaborador {
      value = $colaborador_autenticado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "accessdenied"
      error = "Somente colaboradores ativos podem solicitar ferias."
    }
  
    // A data final nao pode ser anterior a data inicial.
    precondition ($input.data_fim >= $input.data_inicio) {
      error_type = "inputerror"
      error = "A data final deve ser igual ou posterior a data inicial."
    }

    // Regras de ferias da CLT (change ponto-rep-p-e-ferias-clt, tarefa 6.1; spec "Ferias pela CLT"). A situacao (saldo,
    // periodos e dias vendidos da janela da data de inicio) vem de ConectaHR/situacao_ferias, a mesma conta de
    // minha_situacao_ferias. Os limites vem da matriz regra_contrato do contrato da pessoa.
    var $inicio_texto {
      value = $input.data_inicio|to_timestamp|format_timestamp:"Y-m-d":"UTC"
    }

    function.run "ConectaHR/situacao_ferias" {
      input = {colaborador_id: $colaborador_autenticado.id, data_referencia: $inicio_texto}
    } as $situacao

    var $hoje_texto {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    // Todas as regras (antecedencia, periodo aquisitivo, venda, periodos, minimo, saldo, restante utilizavel, periodo
    // de 14 e inicio fora dos dois dias antes de feriado ou domingo) ficam em ConectaHR/validar_pedido_ferias.
    function.run "ConectaHR/validar_pedido_ferias" {
      input = {situacao: $situacao, data_inicio: $inicio_texto, data_fim: ($input.data_fim|to_timestamp|format_timestamp:"Y-m-d":"UTC"), quantidade_dias: $input.quantidade_dias, dias_abono: $input.dias_abono, hoje: $hoje_texto}
    } as $validacao_pedido

    precondition ($validacao_pedido.erro == null) {
      error_type = "inputerror"
      error = $validacao_pedido.erro
    }

    var $dias_abono {
      value = ($input.dias_abono != null ? $input.dias_abono : 0)
    }

    var $restante {
      value = $validacao_pedido.saldo_restante
    }
    // Verifica se ja existe uma solicitacao pendente.
    db.query ferias {
      where = $db.ferias.colaborador_id == $colaborador_autenticado.id && $db.ferias.status == "Pendente"
      return = {type: "single"}
    } as $solicitacao_pendente

    precondition ($solicitacao_pendente == null) {
      error_type = "inputerror"
      error = "Ja existe uma solicitacao de ferias pendente para este colaborador."
    }

    var $regra_aplicavel {
      value = {id: $situacao.regra_id}
    }

    // Cria a solicitacao com o status exato do Enum.
    var $regra_aplicavel_id {
      value = ($regra_aplicavel != null ? $regra_aplicavel.id : null)
    }

    db.add ferias {
      data = {
        colaborador_id  : $colaborador_autenticado.id
        data_solicitacao: "now"
        data_inicio     : $input.data_inicio
        data_fim        : $input.data_fim
        quantidade_dias : $input.quantidade_dias
        dias_abono      : $dias_abono
        observacao_colaborador: $input.observacao
        status          : "Pendente"
        regra_contrato_id: $regra_aplicavel_id
        updated_at      : "now"
      }
    } as $solicitacao_criada

    // Avisa quem decide o pedido (parte 2 das notificacoes, 12/10/2026).
    function.run "ConectaHR/notificar_decisores" {
      input = {colaborador_id: $colaborador_autenticado.id, autor_user_id: $usuario_autenticado.id, quem: "superior", tipo: "pedido_novo", titulo: "Pedido de férias", mensagem: $colaborador_autenticado.nome ~ " pediu férias de " ~ ($input.data_inicio|format_timestamp:"d/m/Y":"UTC") ~ " a " ~ ($input.data_fim|format_timestamp:"d/m/Y":"UTC") ~ ".", recurso: "ferias", registro_id: $solicitacao_criada.id}
    } as $avisos_decisores
  }

  response = {
    sucesso         : true
    mensagem        : "Solicitacao de ferias criada com sucesso e enviada para analise."
    solicitacao     : $solicitacao_criada
    saldo_restante  : $restante
  }

  guid = "ptQRsxyItifAF-IRd7jxeFPRPes"
}