# Anexo de arquivo em Documentos (change `anexo-de-arquivos`)

**Data:** 13/10/2026. **Ambiente:** Xano da equipe (workspace 147338) e projeto do Supabase da equipe, região São Paulo, bucket privado `documentos`.

## Configuração

| Cenário | Esperado | Obtido |
|---|---|---|
| Variáveis no Xano: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ARQUIVOS_DOMINIOS_APROVADOS` | As três definidas; o host do projeto na lista de domínios aprovados | Igual |
| Papel da chave (lido de dentro da chave pelo Xano, sem mostrá-la) | `service_role` | Primeiro `anon` (o envio foi recusado por "row-level security"); depois da troca, `service_role` |
| Chave no formato novo (`sb_secret_...`) | — | Recusada pelo Storage no cabeçalho `Authorization` ("Invalid Compact JWS"); por isso a chave usada é a `service_role` (D2) |

## Envio e abertura

Feito com uma função temporária do Xano que repete as chamadas ao Supabase de `documentos/envio_arquivo` POST e `documentos/{id}/arquivo` GET (depois desativada). Arquivo: uma imagem PNG de 19.865 bytes com a tela de login do sistema, sem dado pessoal.

| # | Cenário | Esperado | Obtido |
|---|---|---|---|
| 1 | Gerar o endereço de envio (`object/upload/sign/documentos/<uuid>.png`) | 200, caminho com UUID e sem dado pessoal | 200 |
| 2 | `PUT` do PNG no endereço de envio | 200 | 200 |
| 3 | `PUT` de novo no mesmo endereço | Recusa (uso único) | 400 |
| 4 | Abrir sem assinatura, pelo endereço público e pelo direto | Recusa (bucket privado) | 400 e 400 |
| 5 | Gerar o link assinado de 300 s (`object/sign/documentos/...`) | 200 | 200 |
| 6 | Abrir pelo link assinado | 200, `image/png`, mesmo conteúdo do original | 200, `image/png`, hash igual |
| 7 | Link assinado com o token adulterado | Recusa | 400 |
| 8 | `PUT` de um arquivo `application/zip` | Recusa (o bucket só aceita PDF, JPEG e PNG) | 400 |

## Não verificado

- As chamadas aos endpoints `documentos/envio_arquivo` e `documentos/{id}/arquivo` com login (dono, RH e o 403 do Gestor): precisam do código de acesso por e-mail. As chamadas ao Supabase que eles fazem são as mesmas da tabela acima.
- O envio pela tela do Streamlit publicado: depende do merge do PR.
