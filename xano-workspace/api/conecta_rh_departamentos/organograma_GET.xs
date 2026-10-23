// Organograma da empresa: visao hierarquica sobre dados ja existentes
// (departamento, cargo, vinculo gestor-colaborador). Nao expõe dados
// sensiveis: cada colaborador aparece apenas com nome, cargo,
// departamento e a URL assinada da foto de perfil, quando houver (change foto-de-perfil). A montagem da hierarquia (departamento -> gestor ->
// colaboradores) fica a cargo do consumidor, cruzando as tres listas
// planas retornadas por id.
query organograma verb=GET {
  api_group = "ConectaRH — Departamentos"
  auth = "user"

  input {
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

    precondition ($usuario_autenticado.ativo) {
      error_type = "unauthorized"
      error = "Usuario inativo."
    }

    precondition ($usuario_autenticado.senha_primeiro_acesso == false) {
      error_type = "unauthorized"
      error = "Troque a senha temporaria antes de continuar."
    }

    // Departamentos ativos, com o colaborador que e gestor de cada um.
    db.query departamento {
      where = $db.departamento.ativo == true
      sort = {departamento.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "gestor_colaborador_id"]
    } as $departamentos

    // Cargos ativos, para resolver o nome do cargo de cada colaborador.
    db.query cargo {
      where = $db.cargo.ativo == true
      return = {type: "list"}
      output = ["id", "nome", "nivel_hierarquico_id", "senioridade", "departamento_id"]
    } as $cargos

    // Niveis ativos, para rotular e ordenar (change organograma-hierarquia, D2).
    db.query nivel_hierarquico {
      where = $db.nivel_hierarquico.ativo == true
      sort = {nivel_hierarquico.ordem: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "ordem"]
    } as $niveis

    // Colaboradores nao desligados (quem esta de ferias ou afastado continua na
    // equipe), somente com os campos permitidos no organograma.
    db.query colaborador {
      where = $db.colaborador.status != "Desligado"
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "cargo_id", "departamento_id", "superior_colaborador_id", "foto_path"]
    } as $colaboradores_brutos

    // Foto de perfil (change foto-de-perfil, D5): URL assinada de 10 minutos, numa chamada so ao Supabase. O caminho
    // no bucket nao sai na resposta; so a URL, e mais nenhum dado pessoal.
    var $caminhos_fotos {
      value = []
    }

    foreach ($colaboradores_brutos) {
      each as $c {
        conditional {
          if ($c.foto_path != null) {
            var.update $caminhos_fotos {
              value = $caminhos_fotos|push:$c.foto_path
            }
          }
        }
      }
    }

    function.run "ConectaHR/assinar_fotos" {
      input = {caminhos: $caminhos_fotos}
    } as $urls_fotos

    var $colaboradores {
      value = []
    }

    foreach ($colaboradores_brutos) {
      each as $c {
        var $url_foto {
          value = ($c.foto_path == null) ? null : ($urls_fotos|get:$c.foto_path)
        }

        var.update $colaboradores {
          value = $colaboradores|push:{id: $c.id, nome: $c.nome, cargo_id: $c.cargo_id, departamento_id: $c.departamento_id, superior_colaborador_id: $c.superior_colaborador_id, foto_url: $url_foto}
        }
      }
    }
  }

  response = {
    sucesso      : true
    departamentos: $departamentos
    cargos       : $cargos
    colaboradores: $colaboradores
    niveis       : $niveis
  }

  guid = "conectahr-organograma-get-0001"
}
