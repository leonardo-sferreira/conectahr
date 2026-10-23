// Avisa um publico inteiro de uma publicacao (change notificacoes-de-publicacao, D1): todos os colaboradores
// nao desligados com conta ativa, ou so os dos departamentos de departamento_ids (",1,4,", o padrao do
// projeto). Fica de fora quem desligou o assunto em "Na plataforma" e o autor da acao. A mesma regra de
// ConectaHR/notificar, mas com tres consultas no total (pessoas, contas ativas e preferencias), e a gravacao
// dentro da mesma chamada (um db.add por pessoa: o db.bulk.add nao existe no XanoScript desta instancia),
// para uma publicacao ser uma requisicao so. Nao audita: quem audita e a acao que publicou.
// Devolve quantos avisos criou.
function "ConectaHR/notificar_publico" {
  input {
    text publico
    text? departamento_ids?
    int? autor_user_id?
    text tipo
    text assunto
    text titulo filters=trim|max:150
    text mensagem filters=trim|max:1000
    text recurso filters=trim|max:50
    int? registro_id?
  }

  stack {
    db.query preferencia_aviso {
      where = $db.preferencia_aviso.assunto == $input.assunto && $db.preferencia_aviso.plataforma == false
      return = {type: "list"}
      output = ["user_id"]
    } as $desligados

    var $desligados_texto {
      value = ","
    }

    foreach ($desligados) {
      each as $d {
        var.update $desligados_texto {
          value = $desligados_texto ~ ($d.user_id|to_text) ~ ","
        }
      }
    }

    db.query user {
      where = $db.user.ativo == true
      return = {type: "list"}
      output = ["id"]
    } as $contas_ativas

    var $ativas_texto {
      value = ","
    }

    foreach ($contas_ativas) {
      each as $c {
        var.update $ativas_texto {
          value = $ativas_texto ~ ($c.id|to_text) ~ ","
        }
      }
    }

    db.query colaborador {
      where = $db.colaborador.status != "Desligado" && $db.colaborador.user_id != null
      return = {type: "list"}
      output = ["user_id", "departamento_id"]
    } as $pessoas

    var $departamentos {
      value = ($input.departamento_ids == null) ? "" : $input.departamento_ids
    }

    var $autor_texto {
      value = ($input.autor_user_id == null) ? "" : ($input.autor_user_id|to_text)
    }

    var $criados {
      value = 0
    }

    foreach ($pessoas) {
      each as $p {
        var $agulha_conta {
          value = "," ~ ($p.user_id|to_text) ~ ","
        }

        var $agulha_departamento {
          value = "," ~ ($p.departamento_id|to_text) ~ ","
        }

        var $no_publico {
          value = ($input.publico == "todos") || ($departamentos|contains:$agulha_departamento)
        }

        conditional {
          if ($no_publico && (($p.user_id|to_text) != $autor_texto) && ($ativas_texto|contains:$agulha_conta) && (($desligados_texto|contains:$agulha_conta) == false)) {
            db.add notificacao_interna {
              data = {
                destinatario_user_id: $p.user_id
                tipo                : $input.tipo
                titulo              : $input.titulo
                mensagem            : $input.mensagem
                recurso             : $input.recurso
                registro_id         : $input.registro_id
              }
            } as $aviso

            var.update $criados {
              value = $criados + 1
            }
          }
        }
      }
    }
  }

  response = $criados

  tags = ["conectahr"]
  guid = "conectahr-notificar-publico-0001"
}
