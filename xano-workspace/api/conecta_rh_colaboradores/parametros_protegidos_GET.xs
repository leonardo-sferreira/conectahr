// Consulta o catalogo de parametros protegidos (item 1.10): para cada
// parametro que uma `regra_override` pode alterar, informa se e
// `configuravel` diretamente pelo RH, exige aprovacao
// (`configuravel_com_aprovacao`) ou nunca pode ser sobrescrito
// (`sem_override`). A aplicacao real desse bloqueio acontece quando o
// endpoint de `regra_override` (item 4.10) for implementado; este
// catalogo e a referencia que aquele endpoint devera consultar.
query parametros_protegidos verb=GET {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou ADMIN podem consultar o catalogo de parametros protegidos."
    }

    db.query parametro_protegido {
      sort = {parametro_protegido.parametro: "asc"}
      return = {type: "list"}
    } as $parametros
  }

  response = {
    sucesso   : true
    parametros: $parametros
  }

  guid = "conectahr-parametros-protegidos-get-0001"
}
