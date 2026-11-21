// Acrescenta a cada reconhecimento os nomes de quem enviou, de quem recebeu e de quem moderou, e o nome da
// competência (tarefa 66 da change concluir-frontend-streamlit). Não muda quem aparece: as rotas chamam depois de
// aplicar as regras de visibilidade. Os nomes de quem envia vêm do usuário (o Admin pode não ter ficha).
function "ConectaHR/enriquecer_reconhecimentos" {
  input {
    json lista
  }

  stack {
    db.query user {
      return = {type: "list"}
      output = ["id", "nome"]
    } as $usuarios

    db.query colaborador {
      return = {type: "list"}
      output = ["id", "nome"]
    } as $colaboradores

    db.query competencia_avaliacao {
      return = {type: "list"}
      output = ["id", "nome"]
    } as $competencias

    var $nome_usuario {
      value = {}
    }

    foreach ($usuarios) {
      each as $u {
        var $chave_u {
          value = "u" ~ ($u.id|to_text)
        }

        var.update $nome_usuario {
          value = $nome_usuario|set:$chave_u:$u.nome
        }
      }
    }

    var $nome_colaborador {
      value = {}
    }

    foreach ($colaboradores) {
      each as $c {
        var $chave_c {
          value = "c" ~ ($c.id|to_text)
        }

        var.update $nome_colaborador {
          value = $nome_colaborador|set:$chave_c:$c.nome
        }
      }
    }

    var $nome_competencia {
      value = {}
    }

    foreach ($competencias) {
      each as $k {
        var $chave_k {
          value = "k" ~ ($k.id|to_text)
        }

        var.update $nome_competencia {
          value = $nome_competencia|set:$chave_k:$k.nome
        }
      }
    }

    var $saida {
      value = []
    }

    foreach ($input.lista) {
      each as $r {
        var $chave_remetente_nome {
          value = "u" ~ ($r.remetente_user_id|to_text)
        }

        var $remetente_nome {
          value = $nome_usuario|get:$chave_remetente_nome
        }

        var $chave_destinatario_nome {
          value = "c" ~ ($r.destinatario_colaborador_id|to_text)
        }

        var $destinatario_nome {
          value = $nome_colaborador|get:$chave_destinatario_nome
        }

        var $chave_competencia_nome {
          value = "k" ~ ($r.competencia_avaliacao_id|to_text)
        }

        var $competencia_nome {
          value = $nome_competencia|get:$chave_competencia_nome
        }

        var $chave_moderador_nome {
          value = "u" ~ ($r.moderado_por_user_id|to_text)
        }

        var $moderador_nome {
          value = $nome_usuario|get:$chave_moderador_nome
        }

        var $item {
          value = $r|set:"remetente_nome":$remetente_nome|set:"destinatario_nome":$destinatario_nome|set:"competencia_nome":$competencia_nome|set:"moderador_nome":$moderador_nome
        }

        var.update $saida {
          value = $saida|push:$item
        }
      }
    }
  }

  response = $saida

  guid = "conectahr-enriquecer-reconhecimentos-0001"
}
