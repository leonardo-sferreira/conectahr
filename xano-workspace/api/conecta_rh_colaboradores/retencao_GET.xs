// Tela "Retenção e anonimização" (Figma 290:902; tarefa 64 da change concluir-frontend-streamlit). Somente leitura,
// RH ou Admin. Devolve numa chamada: os documentos com prazo de guarda vencido (como documentos/retencao_vencida),
// as pessoas da tela (desligados e donos desses documentos) com o desligamento e a anonimização, os prazos de guarda
// dessas pessoas (para o maior "guarda até") e quem tem processo em aberto, pelas mesmas regras que
// colaboradores/{id}/anonimizar confere antes de anonimizar. Não devolve CPF, contato, arquivo nem número de documento.
query "retencao" verb=GET {
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

    var $perfil_autenticado {
      value = $usuario_autenticado.perfil|trim|to_upper
    }

    precondition ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN") {
      error_type = "accessdenied"
      error = "Somente RH ou Admin podem consultar a retencao de dados."
    }

    var $hoje_retencao {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    db.query documento {
      where = $db.documento.retencao_ate != null && $db.documento.retencao_ate < $hoje_retencao
      sort = {documento.retencao_ate: "asc"}
      return = {type: "list"}
      output = ["id", "colaborador_id", "tipo", "nome_documento", "status", "retencao_ate"]
    } as $documentos_vencidos

    db.query colaborador {
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "status", "data_desligamento", "anonimizado_em"]
    } as $todos

    // Quem aparece na tela: os desligados e os donos dos documentos vencidos (ids em texto ",9,12,").
    var $ids {
      value = ","
    }

    foreach ($documentos_vencidos) {
      each as $d {
        var.update $ids {
          value = $ids ~ ($d.colaborador_id|to_text) ~ ","
        }
      }
    }

    var $pessoas {
      value = []
    }

    foreach ($todos) {
      each as $c {
        var $entra {
          value = $c.status == "Desligado" || ($ids|contains:("," ~ ($c.id|to_text) ~ ","))
        }

        conditional {
          if ($entra) {
            var.update $pessoas {
              value = $pessoas|push:$c
            }

            var.update $ids {
              value = $ids ~ ($c.id|to_text) ~ ","
            }
          }
        }
      }
    }

    db.query documento {
      where = $db.documento.retencao_ate != null
      return = {type: "list"}
      output = ["colaborador_id", "retencao_ate"]
    } as $todas_guardas

    var $guardas {
      value = []
    }

    foreach ($todas_guardas) {
      each as $g {
        conditional {
          if ($ids|contains:("," ~ ($g.colaborador_id|to_text) ~ ",")) {
            var.update $guardas {
              value = $guardas|push:$g
            }
          }
        }
      }
    }

    // Processo em aberto: as mesmas condições de colaboradores/{id}/anonimizar.
    db.query ferias {
      where = $db.ferias.status == "Pendente"
      return = {type: "list"}
      output = ["colaborador_id"]
    } as $ferias_abertas

    db.query solicitacao_rh {
      where = $db.solicitacao_rh.status == "recebida" || $db.solicitacao_rh.status == "em_analise"
      return = {type: "list"}
      output = ["colaborador_id"]
    } as $solicitacoes_abertas

    db.query solicitacao_desligamento {
      where = $db.solicitacao_desligamento.status == "pendente" || $db.solicitacao_desligamento.status == "em_analise" || $db.solicitacao_desligamento.status == "agendado"
      return = {type: "list"}
      output = ["colaborador_id"]
    } as $desligamentos_abertos

    var $abertos_txt {
      value = ","
    }

    foreach ($ferias_abertas) {
      each as $fa {
        var.update $abertos_txt {
          value = $abertos_txt ~ ($fa.colaborador_id|to_text) ~ ","
        }
      }
    }

    foreach ($solicitacoes_abertas) {
      each as $sa {
        var.update $abertos_txt {
          value = $abertos_txt ~ ($sa.colaborador_id|to_text) ~ ","
        }
      }
    }

    foreach ($desligamentos_abertos) {
      each as $da {
        var.update $abertos_txt {
          value = $abertos_txt ~ ($da.colaborador_id|to_text) ~ ","
        }
      }
    }

    var $processo_aberto {
      value = []
    }

    foreach ($pessoas) {
      each as $p {
        conditional {
          if ($abertos_txt|contains:("," ~ ($p.id|to_text) ~ ",")) {
            var.update $processo_aberto {
              value = $processo_aberto|push:$p.id
            }
          }
        }
      }
    }
  }

  response = {
    hoje           : $hoje_retencao
    documentos     : $documentos_vencidos
    pessoas        : $pessoas
    guardas        : $guardas
    processo_aberto: $processo_aberto
  }

  guid = "conectahr-retencao-get-0001"
}
