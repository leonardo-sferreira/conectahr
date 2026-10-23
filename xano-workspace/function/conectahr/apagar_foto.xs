// Apaga uma foto de perfil do bucket privado fotos-perfil (change foto-de-perfil, D3 e D4). Caminho vazio ou
// sem a configuracao do Supabase: nao faz nada. Devolve true se o Supabase confirmou.
function "ConectaHR/apagar_foto" {
  input {
    text? caminho?
  }

  stack {
    var $apagou {
      value = false
    }

    conditional {
      if (($input.caminho != null) && ($input.caminho != "") && ($env.SUPABASE_URL != null) && ($env.SUPABASE_SERVICE_KEY != null)) {
        api.request {
          url = ($env.SUPABASE_URL|trim) ~ "/storage/v1/object/fotos-perfil/" ~ $input.caminho
          method = "DELETE"
          headers = ["apikey: " ~ $env.SUPABASE_SERVICE_KEY, "Authorization: Bearer " ~ $env.SUPABASE_SERVICE_KEY]
        } as $resposta_apagar

        var.update $apagou {
          value = $resposta_apagar.response.status == 200
        }
      }
    }
  }

  response = $apagou

  tags = ["conectahr"]
  guid = "conectahr-apagar-foto-0001"
}
