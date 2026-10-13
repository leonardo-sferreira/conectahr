// Cria uma notificacao interna para uma pessoa (sino do topo; parte 2 das notificacoes, 12/10/2026).
// A pessoa vem pelo usuario (destinatario_user_id) ou pelo colaborador (colaborador_id, que acha o
// usuario). Sem conta, ou quando o destinatario e o proprio autor da acao, nao cria nada.
function "ConectaHR/notificar" {
  input {
    int? destinatario_user_id?
    int? colaborador_id?
    int? autor_user_id?
    text tipo
    text titulo filters=trim|max:150
    text mensagem filters=trim|max:1000
    text recurso filters=trim|max:50
    int? registro_id?
  }

  stack {
    var $destino {
      value = $input.destinatario_user_id
    }

    conditional {
      if ($destino == null && $input.colaborador_id != null) {
        db.get colaborador {
          field_name = "id"
          field_value = $input.colaborador_id
        } as $pessoa

        conditional {
          if ($pessoa != null) {
            var.update $destino {
              value = $pessoa.user_id
            }
          }
        }
      }
    }

    var $criada {
      value = false
    }

    conditional {
      if ($destino != null && $destino != $input.autor_user_id) {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $destino
            tipo                : $input.tipo
            titulo              : $input.titulo
            mensagem            : $input.mensagem
            recurso             : $input.recurso
            registro_id         : $input.registro_id
          }
        } as $notificacao

        var.update $criada {
          value = true
        }
      }
    }
  }

  response = $criada

  tags = ["conectahr"]
  guid = "conectahr-notificar-0001"
}
