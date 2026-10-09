// Lista registros de ausencia por status.
// Operacao permitida somente para RH ou ADMIN.
query ausencias verb=GET {
  api_group = "ConectaRH - Ausencias"
  auth = "user"

  input {
    text status filters=trim
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
  
    // Impede consulta por conta inativa.
    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }
  
    // Normaliza o perfil.
    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }
  
    // Somente RH ou ADMIN podem listar todas as ausencias.
    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem listar ausencias."
    }
  
    // Impede filtro vazio.
    precondition ($input.status != "") {
      error_type = "inputerror"
      error = "Informe o status que deseja consultar."
    }
  
    // Lista os registros com o status exato informado.
    db.query ausencia {
      where = $db.ausencia.status == $input.status
      sort = {ausencia.created_at: "desc"}
      // Sem o comprovante (atestado): so abre por ausencias/{id}/comprovante, que audita o acesso.
      output = ["id", "created_at", "updated_at", "colaborador_id", "tipo", "data_inicio", "data_fim", "motivo_tipo", "status", "observacao"]
      return = {type: "list"}
    } as $registros_ausencia
  
    // Conta os registros encontrados.
    var $quantidade {
      value = $registros_ausencia|count
    }
  }

  response = {
    sucesso   : true
    status    : $input.status
    quantidade: $quantidade
    ausencias : $registros_ausencia
  }

  guid = "nejlqda2UnUKYOznpaF0cN4PZy4"
}