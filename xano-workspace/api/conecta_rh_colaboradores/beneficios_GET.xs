// Catalogo de beneficios (tarefa 82). Somente RH ou Admin.
query beneficios verb=GET {
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
      error = "Somente RH ou Admin podem gerenciar beneficios."
    }

    db.query beneficio {
      sort = {beneficio.nome: "asc"}
      return = {type: "list"}
    } as $beneficios

    // Para cada beneficio (tarefa 85): a FAQ e quantas pessoas o tem, para o RH saber quem sera avisado.
    var $hoje {
      value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
    }

    var $itens {
      value = []
    }

    foreach ($beneficios) {
      each as $b {
        db.query beneficio_faq {
          where = $db.beneficio_faq.beneficio_id == $b.id && $db.beneficio_faq.ativo == true
          sort = {beneficio_faq.ordem: "asc"}
          return = {type: "list"}
        } as $faq_do_beneficio

        db.query colaborador_beneficio {
          where = $db.colaborador_beneficio.beneficio_id == $b.id && $db.colaborador_beneficio.ativo == true
          return = {type: "list"}
        } as $vinculos_b

        var $qtd_vigentes {
          value = 0
        }

        var $qtd_personalizados {
          value = 0
        }

        foreach ($vinculos_b) {
          each as $vb {
            conditional {
              if ($vb.data_fim == null || $vb.data_fim >= $hoje) {
                var.update $qtd_vigentes {
                  value = $qtd_vigentes + 1
                }

                conditional {
                  if ($vb.valor_personalizado) {
                    var.update $qtd_personalizados {
                      value = $qtd_personalizados + 1
                    }
                  }
                }
              }
            }
          }
        }

        db.query beneficio_arquivo {
          where = $db.beneficio_arquivo.beneficio_id == $b.id && $db.beneficio_arquivo.ativo == true
          sort = {beneficio_arquivo.id: "asc"}
          output = ["id", "nome"]
          return = {type: "list"}
        } as $materiais_b

        var.update $itens {
          value = $itens|push:{id: $b.id, nome: $b.nome, tipo: $b.tipo, operadora: $b.operadora, descricao: $b.descricao, links: $b.links, arquivos: $materiais_b, ativo: $b.ativo, valor_empresa_padrao: $b.valor_empresa_padrao, desconto_padrao: $b.desconto_padrao, faq: $faq_do_beneficio, qtd_vigentes: $qtd_vigentes, qtd_personalizados: $qtd_personalizados}
        }
      }
    }
  }

  response = {
    sucesso   : true
    beneficios: $itens
  }

  guid = "conectahr-beneficios-get-0001"
}
