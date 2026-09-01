# Templates de e-mail no Brevo — ConectaRH

Antes desta mudança, todo e-mail transacional do ConectaRH era enviado com
conteúdo direto (`textContent`), montado como texto puro dentro do próprio
código XanoScript — não havia nenhum template no Brevo, e qualquer alteração de
visual/texto exigia editar e publicar código. Esta mudança criou 5 templates
transacionais reais no Brevo (via API, `POST /v3/smtp/templates`) e migrou todos
os 11 pontos de envio de e-mail do backend para usá-los via `templateId` +
`params`, em vez de `textContent`.

## Templates criados

| id | nome no Brevo | usado por |
|----|----------------|-----------|
| 1 | `conectahr_outbox_generico` | `email_outbox/processar` (processador único de todos os eventos assíncronos) e `ConectaHR/enviar_email` (função utilitária, hoje sem chamador ativo) |
| 2 | `conectahr_codigo_acesso_login` | `auth/login` |
| 3 | `conectahr_codigo_acesso_reenvio` | `auth/otp/reenviar` |
| 4 | `conectahr_redefinicao_senha` | `auth/senha/esqueci` |
| 5 | `conectahr_documento_pendente` | `pendencias_documento` |

Os ids são numéricos e ficam hardcoded como literal (`templateId: N`) em cada
endpoint — mesmo padrão de constante já usado no projeto para textos de
assunto/mensagem antes desta mudança.

## Por que 5 templates para 11 pontos de envio

Dois envios são síncronos e diretos (login e resgate de senha esquecida, cada
um com seu próprio template). Um envio (`pendencias_documento`) também é
síncrono e direto. Os outros 6 pontos (`auth/login` — alerta de acesso
suspeito, `documentos/processar_vencimentos`, `solicitacoes/{id}/atender`,
`solicitacoes/{id}/indeferir`, `avaliacoes` — avaliação disponível,
`ferias/{id}/aprovar`) não chamam o Brevo diretamente: eles só gravam
`assunto`/`corpo` na tabela `email_outbox`, e é o endpoint
`email_outbox/processar` quem efetivamente chama a API do Brevo, hoje sempre
com o template genérico (id 1), passando `assunto`→`titulo` e `corpo`→`mensagem`
como parâmetros. Migrar esse único endpoint processador cobre os 6 produtores
de uma vez, sem precisar tocar em cada um deles.

## Como editar visualmente

Os 5 templates agora existem no painel do Brevo (Campanhas → Modelos de
e-mail transacional) e podem ser editados por lá — cor, logo, rodapé, texto ao
redor dos placeholders `{{ params.nome }}`, `{{ params.codigo }}`,
`{{ params.titulo }}`, `{{ params.mensagem }}`, `{{ params.tipo_documento }}`,
`{{ params.prazo }}` — sem precisar alterar ou publicar código XanoScript. Só a
lista de parâmetros disponíveis para cada template (definida em cada endpoint,
ver tabela acima) exige mudança de código caso um novo dado precise ser
exibido.

## Limitação do template genérico (id 1)

O template genérico não tem lógica condicional própria — ele só injeta
`titulo` (vira o assunto e um cabeçalho) e `mensagem` (o corpo, já montado
pelo código de cada produtor, incluindo pontuação e quebras de linha). Isso
significa que o texto específico de cada evento (ex.: "sua solicitação foi
indeferida", "documento vence em 7 dias") continua sendo montado em
XanoScript, não no template — só a moldura visual (marca ConectaRH, rodapé de
aviso automático) passou a viver no Brevo. Um refino futuro poderia dividir o
template genérico em um por tipo de evento (com o texto fixo vivendo 100% no
Brevo e só variáveis nos params), mas isso está fora do escopo desta mudança.

## Verificado ao vivo

- `auth/login`: login completo com senha real + OTP relayado do e-mail real do
  usuário, template `conectahr_codigo_acesso_login` renderizado e validado
  (token emitido com sucesso).
- `auth/otp/reenviar`: aceito pelo Brevo (endpoint tem precondição que bloqueia
  a resposta de sucesso se o Brevo não retornar 2xx — retornou sucesso).
- `auth/senha/esqueci`: mesma precondição de sucesso, retornou a mensagem
  genérica esperada (Brevo aceitou o envio).
- `pendencias_documento`: criada pendência real para colaborador de teste,
  notificação disparada sem erro.
- `email_outbox/processar`: processou o lote real de 9 e-mails pendentes
  acumulados de testes anteriores (alertas, decisões de solicitação/férias,
  avaliação disponível) — 9 de 9 enviados com sucesso via template genérico,
  0 falhas.
