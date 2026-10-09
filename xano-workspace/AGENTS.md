# AGENTS.md — xano-workspace (backend)

Regras específicas do backend em XanoScript. Fluxo de trabalho, segredos, LGPD, testes e idioma
estão no [`AGENTS.md` da raiz](../AGENTS.md) e valem aqui. O checklist de endpoint abaixo é o
mesmo da raiz (seção 5) e o que `tools/checar_endpoints.py` confere.

## Checklist de endpoint

Todo endpoint autenticado (`auth = "user"`), **nesta ordem e antes da primeira escrita**:

1. carregar o usuário com `db.get user` pelo `$auth.id`;
2. `precondition ($usuario.ativo)`;
3. `precondition ($usuario.senha_primeiro_acesso == false)`, exceto nas rotas de troca de senha,
   `auth/me`, logout e sessões;
4. validar a sessão do token: `db.get sessao` pelo `$auth.extras.sessao_id` e `precondition`
   de sessão ativa, do próprio usuário, não revogada e não expirada.

Depois: autorização por perfil e escopo; auditoria de toda escrita (mascarada); `output`
explícito com dado sensível; mensagens em português; `python tools/checar_endpoints.py` antes de
publicar. A guarda é **replicada em cada endpoint** (decisão do `design.md` do
`conectarh.gestao`): não há middleware compartilhado.

Para copiar o padrão, use um endpoint recente como modelo, por exemplo
`api/conecta_rh_colaboradores/ciclos_avaliacao_POST.xs`.

## Padrões de XanoScript adotados

- **`precondition`:** erro com `error_type` (`unauthorized`, `accessdenied`, `notfound`,
  `inputerror`, `toomanyrequests`) e mensagem em português. Autorização vem **antes** de
  existência e de estado, para não vazar se um registro existe. Condições compostas com `&&` e
  `||` levam parênteses próprios em cada comparação.
- **"Registra e depois falha":** quando uma tentativa bloqueada precisa de rastro (ex.:
  autoaprovação), grava a auditoria e só então falha com `precondition (false)`. Se a falha
  viesse antes, a auditoria seria desfeita.
- **Auditoria inline:** `db.add auditoria` no próprio endpoint, depois da escrita, com `acao`,
  `recurso`, `registro_id`, `resultado` e, quando útil, `justificativa`, `valor_anterior` e
  `valor_novo` **mascarados**. Nunca senha, token ou código de acesso.
- **Outbox de e-mail:** e-mail assíncrono grava em `email_outbox` com `chave_idempotencia`;
  `email_outbox/processar` (RH/Admin) envia pela Brevo, com tentativas. E-mail síncrono (login e
  senha) usa a Brevo direto e falha o endpoint se o envio falhar.
- **Rotina manual:** o plano não tem tarefas agendadas. O trabalho que depende de data fica em
  `rotinas/processar_diarias` (lógica em `function/conectahr/processar_transicoes_diarias.xs`),
  acionado por RH/Admin, idempotente, e `status_operacional` mostra o que está pendente. Arquivos
  em `task/` ficam `active = false` e não são publicáveis.
- **Append-only:** banco de horas, check-ins e histórico profissional não são editados nem
  apagados; correção é um novo registro. Exclusão física é evitada: arquive ou anonimize.
- **Função em endpoint:** `function.run "ConectaHR/<nome>"` funciona a partir de endpoint;
  evite chamar função a partir de função.

## Armadilhas conhecidas deste workspace

- Os filtros `regex_*` não funcionam (devolvem falso ou vazio sem erro). Valide texto com
  `split`, `substr`, `contains`, `replace`, `strlen`.
- `now|to_text` em campo de dado vira o texto "now". Use `"now"` literal no `data = {}` ou
  `format_timestamp`.
- Campos `date` são texto "Y-m-d": compare com `format_timestamp:"Y-m-d":"UTC"` e converta com
  `to_timestamp` para fazer conta. As datas são sempre em UTC (à noite no Brasil, "hoje" já é
  o dia seguinte).
- Um `||` entre parênteses dentro de `where` de `db.query` não filtrou direito: filtre no laço.
- `db.get` com `output` restrito não traz os outros campos: inclua o que o endpoint usa.
- `db.get` com `field_value` nulo falha: confira antes.
- Variável de ambiente não definida vale `null`: trate o padrão (`$env.X != null ? ... : padrão`).
- Upload de arquivo privado (`image`, `attachment`, `file`) não é suportado no plano atual.
- Cada `swagger = {active: false}` dos 10 grupos é obrigatório (o checker reprova o contrário).

## Fluxo de publicação

Sempre com o perfil `-p ConectaRH`. **Cite os padrões `-i` e `-e` entre aspas** (sem aspas o
shell expande a lista) e exclua os arquivos de grupo, que carregam a configuração do swagger.

```
xano workspace push -p ConectaRH -i "api/conecta_rh_ponto/**/*.xs" -e "api/*/conecta_rh_*.xs" --dry-run
xano workspace push -p ConectaRH -i "api/conecta_rh_ponto/**/*.xs" -e "api/*/conecta_rh_*.xs" --force
xano workspace pull -p ConectaRH -d <pasta-temporaria>        # e diff com o repositório
```

1. `--dry-run` primeiro, e conferir `Matched`/`Kept` e a lista `UPDATE`/`CREATE`/`DELETE`: só
   devem aparecer os arquivos que você mudou.
2. Mudança de schema (campo de tabela) vai em push **separado**, com `ADD_FIELD`/`UPDATE_FIELD`
   no dry-run e nenhuma remoção.
3. Depois do push, teste por HTTP e rode `python tools/checar_endpoints.py`.
4. **Nunca** `--sync --delete` nem `--truncate` sem o dry-run completo e a autorização de quem
   responde pelo projeto: excluir `api/**` ou `table/**` do filtro faz o dry-run apagar tudo.
5. O diff pós-`pull` mostra diferenças só de formatação; ignore-as.

## Verificador de endpoints

`python tools/checar_endpoints.py` (todo o workspace), `--grupo conecta_rh_ponto` (um grupo) e
`--sem-sessao` (ignora o item 4). Ele confere os itens 1 a 4 do checklist, a ordem em relação à
primeira escrita e o `swagger` dos grupos, e sai com código 1 se algo falhar. Aceitar uma
exceção nova (rota livre de primeiro acesso) exige registro no `design.md` e na lista do script.
