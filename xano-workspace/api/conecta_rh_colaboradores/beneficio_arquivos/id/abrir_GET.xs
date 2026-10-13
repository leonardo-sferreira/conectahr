// Abre um material de beneficio (change apresentacao-de-beneficios, D2): link assinado de 5 minutos no Supabase.
// RH e Admin abrem qualquer material; o colaborador, so os dos beneficios que tem ativos (vinculo vigente).
// Cada abertura e auditada.
query "beneficio_arquivos/{id}/abrir" verb=GET {
  api_group = "ConectaRH — Colaboradores"
  auth = "user"

  input {
    int id
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
    db.get beneficio_arquivo {
      field_name = "id"
      field_value = $input.id
    } as $material

    precondition ($material != null && $material.ativo) {
      error_type = "notfound"
      error = "Material nao encontrado."
    }

    var $pode_abrir {
      value = ($perfil_autenticado == "RH" || $perfil_autenticado == "ADMIN")
    }

    conditional {
      if ($pode_abrir == false) {
        db.get colaborador {
          field_name = "user_id"
          field_value = $usuario_autenticado.id
        } as $colaborador_autenticado

        conditional {
          if ($colaborador_autenticado != null) {
            var $hoje {
              value = now|format_timestamp:"Y-m-d":"America/Sao_Paulo"
            }

            db.query colaborador_beneficio {
              where = $db.colaborador_beneficio.colaborador_id == $colaborador_autenticado.id && $db.colaborador_beneficio.beneficio_id == $material.beneficio_id && $db.colaborador_beneficio.ativo == true
              return = {type: "list"}
            } as $vinculos_material

            foreach ($vinculos_material) {
              each as $vinculo_material {
                conditional {
                  if ($vinculo_material.data_fim == null || $vinculo_material.data_fim >= $hoje) {
                    var.update $pode_abrir {
                      value = true
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    precondition ($pode_abrir) {
      error_type = "accessdenied"
      error = "Este material e de um beneficio que voce nao tem."
    }

    // Mesmos cabecalhos de documentos/envio_arquivo: a chave service_role vai no apikey e no Authorization.
    precondition ($env.SUPABASE_URL != null && $env.SUPABASE_SERVICE_KEY != null) {
      error_type = "standard"
      error = "O envio de arquivos ainda nao foi configurado. Fale com o RH."
    }

    var $base_supabase {
      value = $env.SUPABASE_URL|trim
    }
    api.request {
      url = $base_supabase ~ "/storage/v1/object/sign/documentos/" ~ $material.caminho
      method = "POST"
      headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
      params = {expiresIn: 300}
    } as $resposta_assinatura

    precondition ($resposta_assinatura.response.status == 200 && $resposta_assinatura.response.result.signedURL != null) {
      error_type = "standard"
      error = "Nao foi possivel abrir o material agora. Tente de novo em instantes."
    }

    db.add auditoria {
      data = {
        user_id    : $usuario_autenticado.id
        acao       : "abrir_material_beneficio"
        recurso    : "beneficio_arquivo"
        registro_id: $material.id
        resultado  : "sucesso"
      }
    } as $evento_auditoria
  }

  response = {
    sucesso           : true
    nome              : $material.nome
    arquivo_url       : $base_supabase ~ "/storage/v1" ~ $resposta_assinatura.response.result.signedURL
    expira_em_segundos: 300
  }
  guid = "UVPxUdYzvrA-SkJ8htez2NGhtNw"
}