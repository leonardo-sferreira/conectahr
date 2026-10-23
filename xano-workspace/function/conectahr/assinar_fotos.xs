// URLs assinadas das fotos de perfil (change foto-de-perfil, D5): recebe a lista de caminhos do bucket privado
// fotos-perfil e devolve um objeto {caminho: url}, numa chamada so ao Supabase (assinatura em lote), com validade
// de 10 minutos. Caminho vazio ou que o Supabase nao assina fica de fora. Sem a configuracao do Supabase, devolve
// um objeto vazio: a tela mostra as iniciais.
function "ConectaHR/assinar_fotos" {
  input {
    json caminhos
  }

  stack {
    var $urls {
      value = {}
    }

    conditional {
      if (($env.SUPABASE_URL != null) && ($env.SUPABASE_SERVICE_KEY != null) && (($input.caminhos|count) > 0)) {
        var $base_supabase {
          value = $env.SUPABASE_URL|trim
        }

        api.request {
          url = $base_supabase ~ "/storage/v1/object/sign/fotos-perfil"
          method = "POST"
          headers = ["Content-Type: application/json", "apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
          params = {expiresIn: 600, paths: $input.caminhos}
        } as $resposta_assinatura

        conditional {
          if ($resposta_assinatura.response.status == 200) {
            foreach ($resposta_assinatura.response.result) {
              each as $item {
                conditional {
                  if (($item.signedURL != null) && ($item.path != null)) {
                    var $url_assinada {
                      value = $base_supabase ~ "/storage/v1" ~ $item.signedURL
                    }

                    var $caminho_item {
                      value = $item.path
                    }

                    var.update $urls {
                      value = $urls|set:$caminho_item:$url_assinada
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  response = $urls

  tags = ["conectahr"]
  guid = "conectahr-assinar-fotos-0001"
}
