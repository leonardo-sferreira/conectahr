// Treinamentos para o RH (change treinamentos-obrigatorios, D2), numa chamada: o catalogo (ativos e inativos),
// todas as conclusoes, as pessoas nao desligadas (id, nome, departamento) e os departamentos ativos. A matriz
// (pessoa x obrigatorio) e as situacoes saem na tela. So RH e Admin.
query "treinamentos" verb=GET {
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

    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    precondition (($perfil_autenticado == "RH") || ($perfil_autenticado == "ADMIN")) {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem fazer isso."
    }

    db.query treinamento {
      sort = {treinamento.nome: "asc"}
      return = {type: "list"}
    } as $catalogo

    db.query treinamento_conclusao {
      sort = {treinamento_conclusao.concluido_em: "desc"}
      return = {type: "list"}
      output = ["id", "treinamento_id", "colaborador_id", "concluido_em", "valido_ate", "instrutor", "certificado_url"]
    } as $conclusoes

    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "departamento_id"]
    } as $pessoas

    db.query departamento {
      where = $db.departamento.ativo == true
      sort = {departamento.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome"]
    } as $departamentos
  }

  response = {
    sucesso      : true
    hoje         : $hoje
    treinamentos : $catalogo
    conclusoes   : $conclusoes
    pessoas      : $pessoas
    departamentos: $departamentos
  }

  guid = "conectahr-treinamentos-get-0001"
}
