// Cria uma solicitação de desligamento.
// O colaborador pode solicitar o próprio desligamento.
// O Gestor pode solicitar desligamento somente de colaboradores
// pertencentes a um departamento sob sua responsabilidade.
query solicitacoes_desligamento verb=POST {
  api_group = "ConectaRH — Desligamentos"
  auth = "user"

  input {
    int colaborador_id
    text tipo_desligamento filters=trim
    date data_prevista
    int dias_aviso filters=min:0
    text motivo_solicitacao filters=trim|min:5|max:1000
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
  
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuário inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Localiza o colaborador vinculado ao solicitante.
    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_solicitante
  
    precondition ($colaborador_solicitante != null) {
      error_type = "notfound"
      error = "Não existe um colaborador vinculado à conta autenticada."
    }
  
    // O solicitante precisa estar profissionalmente ativo.
    var $status_solicitante {
      value = $colaborador_solicitante.status|trim|to_upper
    }
  
    precondition ($status_solicitante == "ATIVO") {
      error_type = "accessdenied"
      error = "Um colaborador desligado ou inativo não pode criar solicitações."
    }
  
    // Normaliza o perfil.
    var $perfil_solicitante {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente Colaborador ou Gestor podem abrir a solicitação.
    precondition ($perfil_solicitante == "COLABORADOR" || $perfil_solicitante == "GESTOR") {
      error_type = "accessdenied"
      error = "Somente colaboradores ou gestores podem criar solicitações de desligamento."
    }
  
    // Localiza o colaborador que será desligado.
    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo
  
    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador informado não encontrado."
    }
  
    // O colaborador-alvo precisa estar ativo.
    var $status_colaborador_alvo {
      value = $colaborador_alvo.status|trim|to_upper
    }
  
    precondition ($status_colaborador_alvo == "ATIVO") {
      error_type = "inputerror"
      error = "Só é possível solicitar o desligamento de um colaborador ativo."
    }
  
    // Colaborador comum só pode solicitar o próprio desligamento.
    precondition ($perfil_solicitante == "GESTOR" || $colaborador_alvo.id == $colaborador_solicitante.id) {
      error_type = "accessdenied"
      error = "O colaborador só pode solicitar o próprio desligamento."
    }
  
    // Localiza o departamento do colaborador-alvo.
    db.get departamento {
      field_name = "id"
      field_value = $colaborador_alvo.departamento_id
    } as $departamento_alvo
  
    precondition ($departamento_alvo != null) {
      error_type = "notfound"
      error = "O departamento do colaborador não foi encontrado."
    }
  
    // Gestor só pode solicitar desligamento em departamento
    // pelo qual seja responsável.
    precondition ($perfil_solicitante != "GESTOR" || $departamento_alvo.gestor_colaborador_id == $colaborador_solicitante.id) {
      error_type = "accessdenied"
      error = "O gestor só pode solicitar desligamentos de colaboradores do próprio departamento."
    }
  
    // Normaliza o tipo de desligamento.
    var $tipo_desligamento_normalizado {
      value = $input.tipo_desligamento|trim|to_lower
    }
  
    precondition ($tipo_desligamento_normalizado == "imediato" || $tipo_desligamento_normalizado == "aviso_previo") {
      error_type = "inputerror"
      error = "Tipo de desligamento inválido. Use imediato ou aviso_previo."
    }
  
    // Desligamento imediato usa zero dias de aviso.
    precondition ($tipo_desligamento_normalizado != "imediato" || $input.dias_aviso == 0) {
      error_type = "inputerror"
      error = "No desligamento imediato, dias_aviso deve ser zero."
    }
  
    // Aviso prévio precisa possuir pelo menos um dia.
    precondition ($tipo_desligamento_normalizado != "aviso_previo" || $input.dias_aviso > 0) {
      error_type = "inputerror"
      error = "No aviso prévio, dias_aviso deve ser maior que zero."
    }
  
    // Verifica solicitação pendente para o colaborador.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.colaborador_id == $colaborador_alvo.id && $db.solicitacao_desligamento.status == "pendente"
      return = {type: "single"}
    } as $solicitacao_pendente
  
    precondition ($solicitacao_pendente == null) {
      error_type = "inputerror"
      error = "Já existe uma solicitação pendente para este colaborador."
    }
  
    // Verifica solicitação em análise ainda não decidida.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.colaborador_id == $colaborador_alvo.id && $db.solicitacao_desligamento.status == "em_analise"
      return = {type: "single"}
    } as $solicitacao_em_analise

    precondition ($solicitacao_em_analise == null) {
      error_type = "inputerror"
      error = "Já existe uma solicitação em análise para este colaborador."
    }
  
    // Verifica desligamento agendado.
    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.colaborador_id == $colaborador_alvo.id && $db.solicitacao_desligamento.status == "agendado"
      return = {type: "single"}
    } as $solicitacao_agendada
  
    precondition ($solicitacao_agendada == null) {
      error_type = "inputerror"
      error = "Já existe um desligamento agendado para este colaborador."
    }
  
    // Define a origem da solicitação.
    // A expressão precisa permanecer em uma única linha.
    var $origem_solicitacao {
      value = ($perfil_solicitante == "GESTOR" ? "gestor" : "funcionario")
    }
  
    // Cria a solicitação.
    // O banco aplica pendente como status padrão.
    db.add solicitacao_desligamento {
      data = {
        colaborador_id     : $colaborador_alvo.id
        solicitante_user_id: $usuario_autenticado.id
        origem             : $origem_solicitacao
        tipo_desligamento  : $tipo_desligamento_normalizado
        data_prevista      : $input.data_prevista
        dias_aviso         : $input.dias_aviso
        motivo_solicitacao : $input.motivo_solicitacao
        updated_at         : "now"
      }
    } as $solicitacao_criada
  }

  response = {
    sucesso    : true
    mensagem   : "Solicitação de desligamento criada com sucesso e enviada para análise do RH."
    solicitacao: $solicitacao_criada
  }

  guid = "CLz5T5yIiZPyly0Vbys2DIdr6BI"
}