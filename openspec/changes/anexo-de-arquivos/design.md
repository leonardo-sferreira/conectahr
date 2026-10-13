# Design

## Contexto

`documentos` POST só aceita `arquivo_url` https de um domínio aprovado (a instância do Xano mais `$env.ARQUIVOS_DOMINIOS_APROVADOS`). `documentos/{id}/arquivo` GET devolve esse link ao dono, ao RH e ao Admin e audita cada abertura. As listagens nunca devolvem o link. O Xano do plano gratuito não recebe arquivo (tarefa 4.27).

## Decisões

### D1. Supabase Storage (decisão do usuário, 13/10/2026)
Tecnologia nova na stack, justificada aqui (AGENTS.md, seção 3). O Supabase Storage tem plano gratuito (1 GB), bucket privado, links assinados com validade e uma API HTTP simples, que o Xano chama com `api.request`, como já faz com o Brevo. Alternativas avaliadas: pagar o plano do Xano (tem custo mensal) e o Cloudflare R2 (configuração mais trabalhosa e cartão no cadastro). Serviços públicos de imagem e links de compartilhamento de nuvem continuam fora: documento pessoal não pode ficar em endereço público.

### D2. A chave fica só no Xano
`SUPABASE_URL` e `SUPABASE_SERVICE_KEY` são variáveis de ambiente do Xano. O Streamlit nunca tem a chave: pede ao Xano um endereço de envio de uso único (`documentos/envio_arquivo` POST) e manda o arquivo para esse endereço. O Xano manda a chave nos cabeçalhos `apikey` e `Authorization: Bearer` (os dois com o mesmo valor, o que vale para a chave antiga `service_role` e para a nova `sb_secret_...`).

### D3. Fluxo de envio
1. A tela valida o tipo (PDF, JPG ou PNG) e o tamanho (até 10 MB).
2. `documentos/envio_arquivo` POST com a extensão. O Xano confere a sessão e o perfil (quem pode cadastrar documento: o próprio colaborador ativo, o RH ou o Admin), gera o caminho `<uuid>.<extensão>` e pede ao Supabase `object/upload/sign/documentos/<caminho>`. Devolve `upload_url` e `arquivo_url` (`<SUPABASE_URL>/storage/v1/object/documentos/<caminho>`).
3. A tela envia o arquivo com `PUT upload_url` (o endereço vale uma vez e por pouco tempo).
4. A tela chama `documentos` POST como hoje, com o `arquivo_url`. O domínio do Supabase entra em `ARQUIVOS_DOMINIOS_APROVADOS`, então a regra de domínio aprovado continua igual.

### D4. Abertura com link assinado
`documentos/{id}/arquivo` GET, depois da autorização, olha o `arquivo_url`: se começar por `<SUPABASE_URL>/storage/v1/object/documentos/`, pede ao Supabase `object/sign/documentos/<caminho>` com `expiresIn: 300` e devolve o link assinado. Os links antigos voltam como estão. A auditoria de abertura não muda. Como o RH abre pela Conferência de documentos e a pessoa pela tela Documentos, as duas telas passam a abrir os arquivos anexados sem mudança.

### D5. Nome aleatório no caminho
O caminho é um UUID gerado pelo Xano, sem nome, CPF ou tipo do documento. O link do arquivo não é devolvido nas listagens, e o bucket é privado: sem o link assinado, o endereço não abre.

### D6. Verificação do arquivo
O bucket é configurado com limite de 10 MB e só `application/pdf`, `image/jpeg` e `image/png`, então o Supabase recusa o resto. A verificação de extensão de `verificar_arquivo_documento` continua valendo (o caminho termina com a extensão). O HEAD dessa verificação não tem a chave e não confirma o tamanho de arquivo privado; nesse caso a função já libera sem bloquear, e o limite fica com o bucket.

### D7. Configuração (feita pela equipe, fora do repositório)
No Supabase: projeto na região São Paulo (`sa-east-1`), bucket privado `documentos` com limite de 10 MB e os três tipos acima. No Xano (Settings > Environment Variables): `SUPABASE_URL` (ex.: `https://<projeto>.supabase.co`), `SUPABASE_SERVICE_KEY` e o host do projeto em `ARQUIVOS_DOMINIOS_APROVADOS`. A chave não é colada em conversa, terminal nem arquivo do repositório.

## Riscos

- **Chave vazada dá acesso a todos os arquivos.** Mitigação: só no ambiente do Xano; se aparecer em algum lugar, gerar outra no Supabase.
- **Sem a configuração**, o envio falha com a mensagem "O envio de arquivos ainda não foi configurado. Fale com o RH." e nada é gravado.
- **Arquivo enviado sem documento** (a pessoa fecha a tela entre o envio e o cadastro): fica no bucket sem uso. Aceito nesta change.
