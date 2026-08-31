// RH/ADMIN consultam admissoes CLT cujo eSocial ou CTPS Digital ainda
// nao foi confirmado, com o prazo aplicavel (item 3.5). So sinaliza a
// pendencia — nao chama nenhum servico externo.
query "admissoes_pendentes_esocial_ctps" verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar pendencias de eSocial/CTPS."
    }

    db.query historico_profissional {
      where = $db.historico_profissional.tipo_alteracao == "admissao" && $db.historico_profissional.tipo_contrato == "CLT" && (($db.historico_profissional.esocial_status != "confirmado") || ($db.historico_profissional.ctps_status != "confirmado"))
      sort = {historico_profissional.data_inicio: "asc"}
      return = {type: "list"}
    } as $admissoes_pendentes

    var $total_pendentes {
      value = ($admissoes_pendentes|count)
    }
  }

  response = {
    sucesso            : true
    total_pendentes     : $total_pendentes
    admissoes_pendentes : $admissoes_pendentes
  }

  guid = "conectahr-admissoes-pendentes-esocial-ctps-0001"
}
