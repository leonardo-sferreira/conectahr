// Organograma da empresa: visao hierarquica sobre dados ja existentes
// (departamento, cargo, vinculo gestor-colaborador). Nao expõe dados
// sensiveis: cada colaborador aparece apenas com nome, cargo e
// departamento. A montagem da hierarquia (departamento -> gestor ->
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
      output = ["id", "nome"]
    } as $cargos

    // Colaboradores ativos, somente com os campos permitidos no organograma.
    db.query colaborador {
      where = $db.colaborador.status == "Ativo"
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "cargo_id", "departamento_id"]
    } as $colaboradores
  }

  response = {
    sucesso      : true
    departamentos: $departamentos
    cargos       : $cargos
    colaboradores: $colaboradores
  }

  guid = "conectahr-organograma-get-0001"
}
