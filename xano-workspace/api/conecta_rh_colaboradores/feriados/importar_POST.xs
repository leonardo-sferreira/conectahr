// RH/ADMIN importa os feriados nacionais de um ano da BrasilAPI (change ponto-rep-p-e-ferias-clt,
// tarefa 7.1). So grava as datas que ainda nao tem feriado nacional; repetir nao duplica.
// A regra fica em ConectaHR/importar_feriados_nacionais.
query "feriados/importar" verb=POST {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int ano
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
      error = "Somente RH ou ADMIN podem importar feriados."
    }

    function.run "ConectaHR/importar_feriados_nacionais" {
      input = {ano: $input.ano}
    } as $resultado

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "importar_feriados"
        recurso    : "feriado"
        valor_novo : "ano=" ~ ($input.ano|to_text) ~ "; importados=" ~ (($resultado.importados|count)|to_text) ~ "; ja_existiam=" ~ ($resultado.ja_existiam|to_text) ~ "; fonte=BrasilAPI"
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso    : true
    mensagem   : "Feriados nacionais importados."
    ano        : $input.ano
    importados : $resultado.importados|count
    ja_existiam: $resultado.ja_existiam
  }

  guid = "conectahr-feriados-importar-post-0001"
}
