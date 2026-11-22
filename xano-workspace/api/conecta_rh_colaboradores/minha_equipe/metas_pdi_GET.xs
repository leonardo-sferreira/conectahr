// Metas, PDI e reunioes 1:1 dos liderados diretos (concluir-metas-pdi-equipe, D1). So o minimo: de cada
// meta e acao de PDI, titulo, prazo, progresso e situacao; nunca salario, avaliacao ou dado pessoal. Liderado
// direto: a ficha cujo superior e a ficha do autenticado. Tambem as reunioes 1:1 que o autenticado registrou, os
// ciclos em andamento e as pessoas para quem ele pode criar meta (liderados diretos e o departamento de que e
// gestor, D2). Qualquer perfil com ficha: sem liderados, as listas vem vazias.
query "minha_equipe/metas_pdi" verb=GET {
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    precondition ($colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    db.query colaborador {
      where = $db.colaborador.superior_colaborador_id == $colaborador_autenticado.id && $db.colaborador.status != "Desligado"
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "user_id"]
    } as $liderados

    var $metas {
      value = []
    }

    var $pdis {
      value = []
    }

    foreach ($liderados) {
      each as $liderado {
        db.query meta_avaliacao {
          where = $db.meta_avaliacao.colaborador_id == $liderado.id && $db.meta_avaliacao.status != "cancelada"
          sort = {meta_avaliacao.data_prazo: "asc"}
          return = {type: "list"}
          output = ["id", "colaborador_id", "ciclo_avaliacao_id", "titulo", "data_prazo", "progresso_percentual", "status", "data_checkin_realizado"]
        } as $metas_liderado

        foreach ($metas_liderado) {
          each as $meta_item {
            var.update $metas {
              value = $metas|push:$meta_item
            }
          }
        }

        db.query pdi {
          where = $db.pdi.colaborador_id == $liderado.id && $db.pdi.status != "cancelado"
          sort = {pdi.data_prazo: "asc"}
          return = {type: "list"}
          output = ["id", "colaborador_id", "titulo", "data_prazo", "progresso_percentual", "status"]
        } as $pdis_liderado

        foreach ($pdis_liderado) {
          each as $pdi_item {
            var.update $pdis {
              value = $pdis|push:$pdi_item
            }
          }
        }
      }
    }

    db.query reuniao_individual {
      where = $db.reuniao_individual.gestor_user_id == $usuario_autenticado.id
      sort = {reuniao_individual.data_reuniao: "desc"}
      return = {type: "list"}
      output = ["id", "colaborador_id", "data_reuniao", "hora", "assuntos", "acordos", "situacao", "motivo_cancelamento", "visibilidade"]
    } as $reunioes

    db.query departamento {
      where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id && $db.departamento.ativo == true
      return = {type: "list"}
      output = ["id", "nome"]
    } as $meus_departamentos

    var $pessoas_meta {
      value = []
    }

    foreach ($meus_departamentos) {
      each as $dep {
        db.query colaborador {
          where = $db.colaborador.departamento_id == $dep.id && $db.colaborador.status != "Desligado" && $db.colaborador.id != $colaborador_autenticado.id
          sort = {colaborador.nome: "asc"}
          return = {type: "list"}
          output = ["id", "nome", "user_id"]
        } as $pessoas_dep

        foreach ($pessoas_dep) {
          each as $pessoa_dep {
            var.update $pessoas_meta {
              value = $pessoas_meta|push:$pessoa_dep
            }
          }
        }
      }
    }

    db.query ciclo_avaliacao {
      where = $db.ciclo_avaliacao.status == "em_andamento" && $db.ciclo_avaliacao.ativo == true
      sort = {ciclo_avaliacao.data_inicio: "desc"}
      return = {type: "list"}
      output = ["id", "nome"]
    } as $ciclos
  }

  response = {
    sucesso         : true
    minha_ficha_id  : $colaborador_autenticado.id
    meu_user_id     : $usuario_autenticado.id
    liderados       : $liderados
    metas           : $metas
    pdis            : $pdis
    reunioes        : $reunioes
    pessoas_meta    : $pessoas_meta
    ciclos          : $ciclos
  }

  guid = "conectahr-minha-equipe-metas-pdi-get-0001"
}
