// Define o gestor responsável por um departamento.
// Somente RH ou ADMIN podem realizar esta operação.
query "departamentos/{id}/gestor" verb=PATCH {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
    int id
    int gestor_colaborador_id
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
  
    // Valida o perfil de quem executa a operação.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem definir o gestor de um departamento."
    }
  
    // Localiza o departamento.
    db.get departamento {
      field_name = "id"
      field_value = $input.id
    } as $departamento_alvo
  
    precondition ($departamento_alvo != null) {
      error_type = "notfound"
      error = "Departamento não encontrado."
    }
  
    precondition ($departamento_alvo.ativo) {
      error_type = "inputerror"
      error = "Não é possível definir gestor para um departamento inativo."
    }
  
    // Localiza o colaborador pelo ID recebido.
    db.get colaborador {
      field_name = "id"
      field_value = $input.gestor_colaborador_id
    } as $colaborador_selecionado
  
    precondition ($colaborador_selecionado != null) {
      error_type = "notfound"
      error = "Colaborador selecionado como gestor não encontrado."
    }
  
    // Valida o status profissional.
    var $status_colaborador {
      value = $colaborador_selecionado.status|trim|to_upper
    }
  
    precondition ($status_colaborador == "ATIVO") {
      error_type = "inputerror"
      error = "O colaborador selecionado não está com status ativo."
    }
  
    // Confere o departamento do colaborador.
    precondition ($colaborador_selecionado.departamento_id == $departamento_alvo.id) {
      error_type = "inputerror"
      error = "O colaborador selecionado não pertence a este departamento."
    }
  
    // Confere se existe uma conta vinculada.
    precondition ($colaborador_selecionado.user_id != null) {
      error_type = "inputerror"
      error = "O colaborador selecionado não possui uma conta de acesso vinculada."
    }
  
    // Localiza a conta vinculada ao colaborador.
    db.get user {
      field_name = "id"
      field_value = $colaborador_selecionado.user_id
    } as $conta_do_gestor
  
    precondition ($conta_do_gestor != null) {
      error_type = "notfound"
      error = "A conta de acesso vinculada ao colaborador não foi encontrada."
    }
  
    precondition ($conta_do_gestor.ativo) {
      error_type = "inputerror"
      error = "A conta de acesso do gestor está inativa."
    }
  
    // Confere o perfil da conta.
    var $perfil_da_conta {
      value = $conta_do_gestor.perfil|trim|to_upper
    }
  
    precondition ($perfil_da_conta == "GESTOR") {
      error_type = "inputerror"
      error = "A conta vinculada ao colaborador precisa possuir o perfil Gestor."
    }
  
    // Registra o gestor no departamento.
    db.edit departamento {
      field_name = "id"
      field_value = $departamento_alvo.id
      data = {
        gestor_colaborador_id: $colaborador_selecionado.id
        updated_at           : "now"
      }
    } as $departamento_atualizado
  }

  response = {
    sucesso              : true
    mensagem             : "Gestor definido com sucesso."
    departamento         : $departamento_atualizado
    gestor_colaborador_id: $colaborador_selecionado.id
    gestor_nome          : $colaborador_selecionado.nome
  }

  guid = "ptQz5Oioyl4S1WFXdc1mYych8mk"
}