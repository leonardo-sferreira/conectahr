// Fila de denuncias da comissao de etica (change canal-de-denuncias, D4): todas, das mais novas para as
// mais antigas, com o protocolo, o tipo, o comeco do relato, a data, a situacao, se e identificada e o
// resultado (a identificacao so no detalhe), e as contagens: novas, em apuracao e concluidas no ano.
// So membro ativo da comissao, qualquer que seja o perfil.
query "denuncias" verb=GET {
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

    db.query comissao_etica {
      where = $db.comissao_etica.user_id == $usuario_autenticado.id && $db.comissao_etica.ativo == true
      return = {type: "single"}
    } as $membro_comissao

    precondition ($membro_comissao != null) {
      error_type = "accessdenied"
      error = "So a comissao de etica ve as denuncias."
    }

    db.query denuncia {
      sort = {denuncia.id: "desc"}
      return = {type: "list"}
    } as $todas

    var $ano {
      value = $hoje|substr:0:4
    }

    var $contagens {
      value = {nova: 0, em_apuracao: 0, concluida_no_ano: 0}
    }

    var $denuncias {
      value = []
    }

    foreach ($todas) {
      each as $d {
        conditional {
          if ($d.status == "nova") {
            var.update $contagens {
              value = $contagens|set:"nova":(($contagens|get:"nova") + 1)
            }
          }

          elseif ($d.status == "em_apuracao") {
            var.update $contagens {
              value = $contagens|set:"em_apuracao":(($contagens|get:"em_apuracao") + 1)
            }
          }
        }

        conditional {
          if (($d.status == "concluida") && ($d.concluida_em != null) && ((($d.concluida_em|to_text)|substr:0:4) == $ano)) {
            var.update $contagens {
              value = $contagens|set:"concluida_no_ano":(($contagens|get:"concluida_no_ano") + 1)
            }
          }
        }

        var.update $denuncias {
          value = $denuncias|push:{
            id          : $d.id
            protocolo   : $d.protocolo
            tipo        : $d.tipo
            resumo      : $d.relato|substr:0:140
            recebida_em : $d.recebida_em
            status      : $d.status
            identificada: $d.identificada
            resultado   : $d.resultado
            concluida_em: $d.concluida_em
          }
        }
      }
    }
  }

  response = {
    sucesso  : true
    contagens: $contagens
    denuncias: $denuncias
  }

  guid = "conectahr-denuncias-get-0001"
}
