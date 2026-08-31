// Consulta o contrato especifico (estagio/aprendiz/temporario/PJ) de um
// colaborador (item 3.6). Acesso: RH/ADMIN, ou o proprio colaborador.
query "colaboradores/{id}/contrato_especifico" verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.id
    } as $colaborador_alvo

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    var $e_o_proprio {
      value = ($colaborador_alvo != null && $colaborador_alvo.user_id == $usuario_autenticado.id)
    }

    // Autorizacao checada antes de qualquer estado do colaborador/contrato.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN" || $e_o_proprio) {
      error_type = "accessdenied"
      error = "Voce nao tem permissao para consultar este contrato especifico."
    }

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    db.get contrato_especifico {
      field_name = "colaborador_id"
      field_value = $colaborador_alvo.id
    } as $contrato

    precondition ($contrato != null) {
      error_type = "notfound"
      error = "Este colaborador nao possui um contrato especifico cadastrado."
    }
  }

  response = {
    sucesso : true
    contrato: $contrato
  }

  guid = "conectahr-colaboradores-contrato-especifico-get-0001"
}
