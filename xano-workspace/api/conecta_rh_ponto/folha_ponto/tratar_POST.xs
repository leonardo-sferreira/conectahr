// Ajuste direto do ponto de outra pessoa no REP-P (change ponto-rep-p-e-ferias-clt): o superior
// direto, o Gestor do departamento (para quem nao tem superior), o RH ou o Admin incluem ou
// desconsideram uma marcacao, com motivo, e vale na hora. A marcacao original nao muda: o
// ajuste e um tratamento (Portaria 671/2021, art. 82). Ninguem ajusta o proprio ponto.
// Grava o historico como correcao aprovada, recalcula o dia, audita e avisa a pessoa.
// Substitui folha_ponto/ajustar.
query "folha_ponto/tratar" verb=POST {
  api_group = "ConectaRH - Ponto"
  auth = "user"

  input {
    int colaborador_id
    date data
    enum tipo {
      values = ["inclusao", "desconsideracao"]
    }

    int? marcacao_id?
    timestamp? data_hora?
    text motivo filters=trim|min:5|max:150
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

    db.get colaborador {
      field_name = "user_id"
      field_value = $usuario_autenticado.id
    } as $colaborador_autenticado

    var $ve_todos {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    precondition ($ve_todos || $colaborador_autenticado != null) {
      error_type = "notfound"
      error = "Nao existe um colaborador vinculado a esta conta."
    }

    // Quem a pessoa pode ver (tarefa 81): RH e Admin, todos; os demais, a si mesmos, quem os
    // tem como superior direto e, de quem nao tem superior, o departamento que gerenciam.
    var $departamento_gerido_id {
      value = null
    }

    conditional {
      if ($colaborador_autenticado != null) {
        db.query departamento {
          where = $db.departamento.gestor_colaborador_id == $colaborador_autenticado.id
          return = {type: "single"}
        } as $departamento_gerido

        conditional {
          if ($departamento_gerido != null) {
            var.update $departamento_gerido_id {
              value = $departamento_gerido.id
            }
          }
        }
      }
    }

    db.query colaborador {
      where = $db.colaborador.anonimizado_em == null
      sort = {colaborador.nome: "asc"}
      return = {type: "list"}
      output = ["id", "nome", "departamento_id", "cargo_id", "status", "superior_colaborador_id", "data_admissao", "user_id"]
    } as $todos_colaboradores

    var $visiveis {
      value = []
    }

    var $ids_visiveis {
      value = []
    }

    foreach ($todos_colaboradores) {
      each as $c {
        var $e_eu {
          value = ($colaborador_autenticado != null && $c.id == $colaborador_autenticado.id)
        }

        var $posso_ver {
          value = ($ve_todos || $e_eu || ($colaborador_autenticado != null && ($c.superior_colaborador_id == $colaborador_autenticado.id || ($c.superior_colaborador_id == null && $departamento_gerido_id != null && $c.departamento_id == $departamento_gerido_id))))
        }

        conditional {
          if ($posso_ver) {
            var.update $visiveis {
              value = $visiveis|push:$c
            }

            var.update $ids_visiveis {
              value = $ids_visiveis|push:$c.id
            }
          }
        }
      }
    }

    precondition ($colaborador_autenticado == null || $input.colaborador_id != $colaborador_autenticado.id) {
      error_type = "accessdenied"
      error = "Voce nao pode ajustar o proprio ponto: peca a correcao, que vai para o seu superior."
    }

    precondition ($ids_visiveis|contains:$input.colaborador_id) {
      error_type = "accessdenied"
      error = "Voce nao pode ajustar o ponto desta pessoa."
    }

    db.get colaborador {
      field_name = "id"
      field_value = $input.colaborador_id
    } as $colaborador_alvo

    precondition ($colaborador_alvo != null) {
      error_type = "notfound"
      error = "Colaborador nao encontrado."
    }

    var $hoje_brasilia {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $dia {
      value = $input.data|format_timestamp:"Y-m-d":"UTC"
    }

    precondition ($dia <= $hoje_brasilia) {
      error_type = "inputerror"
      error = "Nao e possivel corrigir um dia futuro."
    }

    precondition ($colaborador_alvo.data_admissao == null || $dia >= ($colaborador_alvo.data_admissao|format_timestamp:"Y-m-d":"UTC")) {
      error_type = "inputerror"
      error = "O dia e anterior a admissao."
    }

    function.run "ConectaHR/validar_tratamento" {
      input = {colaborador_id: $colaborador_alvo.id, data: $dia, tipo: $input.tipo, marcacao_id: $input.marcacao_id, data_hora: $input.data_hora}
    } as $validacao

    // Garante o registro do dia (cache), ao qual o pedido fica ligado.
    function.run "ConectaHR/atualizar_dia_ponto" {
      input = {colaborador_id: $colaborador_alvo.id, data: $dia}
    } as $dia_atual

    db.add tratamento_ponto {
      data = {
        colaborador_id: $colaborador_alvo.id
        data          : $dia
        tipo          : $input.tipo
        marcacao_id   : ($input.tipo == "desconsideracao" ? $input.marcacao_id : null)
        data_hora     : ($input.tipo == "inclusao" ? $input.data_hora : null)
        motivo        : $input.motivo
        autor_user_id : $usuario_autenticado.id
      }
    } as $tratamento_criado

    // Historico: o ajuste fica como correcao ja aprovada, com quem fez e o motivo.
    db.add correcao_ponto {
      data = {
        registro_ponto_id   : $dia_atual.registro.id
        colaborador_id      : $colaborador_alvo.id
        tipo                : $input.tipo
        marcacao_id         : $input.marcacao_id
        valor_solicitado    : ($input.tipo == "inclusao" ? $input.data_hora : null)
        justificativa       : $input.motivo
        status              : "aprovada"
        decidido_por_user_id: $usuario_autenticado.id
        data_decisao        : "now"
        motivo_decisao      : "Ajuste direto"
        updated_at          : "now"
      }
    } as $correcao_registrada

    function.run "ConectaHR/atualizar_dia_ponto" {
      input = {colaborador_id: $colaborador_alvo.id, data: $dia}
    } as $dia_recalculado

    db.add auditoria {
      data = {
        user_id     : $usuario_autenticado.id
        acao        : "tratar_ponto"
        recurso     : "tratamento_ponto"
        registro_id : $tratamento_criado.id
        justificativa: $input.motivo
        valor_novo  : "tipo=" ~ $input.tipo ~ "; dia=" ~ $dia ~ "; colaborador_id=" ~ ($colaborador_alvo.id|to_text)
        resultado   : "sucesso"
      }
    } as $evento_auditoria

    // Avisa a pessoa (quando ela tem conta).
    conditional {
      if ($colaborador_alvo.user_id != null) {
        db.add notificacao_interna {
          data = {
            destinatario_user_id: $colaborador_alvo.user_id
            tipo                : "ponto_ajustado"
            titulo              : "Seu ponto foi ajustado"
            mensagem            : "O dia " ~ ($input.data|format_timestamp:"d/m/Y":"UTC") ~ " teve uma marcacao " ~ ($input.tipo == "inclusao" ? "incluida" : "desconsiderada") ~ ". Motivo: " ~ $input.motivo
            recurso             : "registro_ponto"
            registro_id         : $dia_recalculado.registro.id
          }
        } as $aviso_ajuste
      }
    }
  }

  response = {
    sucesso : true
    mensagem: "Ajuste aplicado. A pessoa foi avisada."
    registro: $dia_recalculado.registro
  }

  guid = "conectahr-folha-ponto-tratar-post-0001"
}
