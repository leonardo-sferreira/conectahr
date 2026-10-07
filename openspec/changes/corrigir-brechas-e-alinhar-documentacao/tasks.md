# Tasks

Convenção (ver `design.md`, D15): cada grupo de tarefas tem um card no Jira (`CON-XX`).
- Branch: `feature/CON-XX-descricao`.
- Commit: `CON-XX <descrição> (<tarefa>)`.
- Pull Request para `master`, com revisão.

Todo push no Xano segue a mesma sequência:
1. `python tools/checar_endpoints.py` sem falhas;
2. `xano workspace push --dry-run`;
3. push real;
4. `xano workspace pull` e diff sem diferença de conteúdo.

As evidências de teste vão para `docs/evidencias/` (tarefa 3.7), sem dados pessoais.

## 1. Brechas de segurança (Parte 1)

- [ ] 1.1 Spike de sessão no token (design D2): emitir um token de teste com `extras = {perfil, sessao_id}` e ler o `sessao_id` num endpoint temporário. Se não houver acessor confiável, testar a alternativa por hash do token. Registrar o resultado em `design.md` (D2). Verificar: o endpoint temporário devolve o `sessao_id` correto para dois tokens diferentes e é removido do workspace ao final. Se as duas abordagens falharem, parar a 1.4 e rever o design antes de seguir.
- [x] 1.2 Criar `tools/checar_endpoints.py` (design D1). O script lista os endpoints com `auth = "user"` sem `db.get user` pelo `$auth.id`, sem `precondition` de `ativo`, sem `senha_primeiro_acesso == false` (fora das 6 exceções) ou sem validação de sessão, e termina com código diferente de zero quando encontra algum. Verificar: rodando no estado atual, ele aponta os 97 endpoints sem checagem de primeiro acesso e os 55 sem checagem de `ativo` da auditoria.
- [x] 1.3 Push do schema aditivo: `user.otp_reenvios`, `user.otp_ultimo_envio_em`, `documento.retencao_ate` e a tabela `resposta_clima_agregado` (índice `"btree|unique"` em pergunta, departamento e nota; sem `created_at`/`updated_at`). Verificar: o dry-run não mostra nenhuma operação destrutiva, o push foi aplicado e o diff pós-pull está limpo.
  - Feito em 2026-10-06 no workspace 147338 (perfil `ConectaRH`). O dry-run mostrou só `ADD_FIELD` e um `CREATE`. O diff pós-pull só tem formatação, mais uma diferença: o Xano descartou os defaults `?=0` de `departamento_id` e `quantidade` em `resposta_clima_agregado`. Sem impacto, porque os dois campos são sempre gravados explicitamente (`responder` e `consolidar_resposta_clima_legado`).
- [ ] 1.4 Sessão no token (item 1.3 da auditoria):
  - `auth/otp/validar` cria a sessão antes do token e inclui o `sessao_id` em `extras`;
  - `auth/logout` encerra exatamente a sessão do token;
  - `auth/sessoes/encerrar_outras` preserva a sessão do token;
  - `auth/sessoes/{id}/encerrar` só encerra sessão do próprio usuário.

  Verificar por HTTP com duas sessões do mesmo usuário: depois do logout na sessão A, o token A é recusado e o token B continua aceito; depois de `encerrar_outras` chamado com B, A é recusado e B continua aceito.
- [ ] 1.5 Guarda de acesso (itens 1.1, 1.2 e 1.3 da auditoria) nos grupos "ConectaRH — Autenticação" e "ConectaRH — Gestão de Usuários": usuário ativo, senha trocada (com as exceções do D1) e sessão válida. Verificar: o script da 1.2 passa para esses grupos. Por HTTP: um usuário com senha temporária só consegue usar `auth/senha PATCH`, `auth/me`, `auth/logout` e as rotas de sessão.
- [ ] 1.6 Guarda de acesso no grupo "ConectaRH — Colaboradores", parte 1: cadastro, organograma, busca, onboarding, contratos, banco de horas, solicitações, comunicados e FAQ. Verificar: o script passa para esses arquivos e o smoke test HTTP funciona com um endpoint por perfil.
- [ ] 1.7 Guarda de acesso no grupo "ConectaRH — Colaboradores", parte 2: avaliação, metas, PDI, clima, reconhecimento, regras, instrumentos, indicadores, auditoria, delegações e calendário. Verificar: o script passa para o grupo inteiro. Por HTTP, com um usuário de senha temporária, `auditoria GET`, `indicadores GET`, `instrumentos_normativos/{id}/aprovar`, `metas POST`, `pdi POST` e `perguntas_clima/{id}/responder` são negados.
- [ ] 1.8 Guarda de acesso nos grupos Ponto, Férias, Ausências, Documentos, Desligamentos, Cargos e Departamentos. Verificar: o script não aponta nenhuma falha em todo o `xano-workspace/api`. Por HTTP, depois de desativar um usuário de teste, o token antigo dele é negado em `ponto/marcar` e em `ferias/solicitacoes`.
- [ ] 1.9 Revogação em massa: `usuarios/{id}/status PATCH` (ao desativar), `solicitacoes_desligamento/{id}/aprovar` (desligamento imediato) e `.../concluir` encerram todas as sessões do usuário, com `revogada_em` preenchido. Verificar por HTTP: o usuário com duas sessões ativas tem os dois tokens recusados depois da desativação.
- [x] 1.10 Reenvio de OTP (item 1.4 da auditoria, design D3):
  - não zerar `otp_tentativas`;
  - bloquear com `otp_tentativas >= 5`, `otp_reenvios >= 3` ou intervalo menor que 60 s;
  - `auth/login` reinicia os contadores;
  - a 5ª tentativa errada em `auth/otp/validar` limpa o `otp_codigo`.

  Verificar por HTTP: depois de 5 códigos errados, o reenvio é recusado; um reenvio feito antes de 60 s é recusado sem enviar e-mail; só um novo login gera código válido.
  - Verificado em 2026-10-06 por HTTP, com a conta Admin de teste:
    - reenvio antes de 60 s → 429;
    - códigos errados 1 a 5 → 403;
    - 6ª tentativa → 403 em vez de 429, o que confirma que o código foi descartado;
    - reenvio depois de 5 erros → 403;
    - novo login e reenvios 1 a 3 com 61 s de intervalo → 200, e o 4º → 429;
    - novo login → código válido e token emitido.

    Evidência formal pendente na 1.17.
- [ ] 1.11 Bloqueio de autoaprovação (item 1.5 da auditoria, design D4) em todos os endpoints de decisão listados no D4, com a auditoria `autoaprovacao_bloqueada` gravada antes da recusa. Verificar por HTTP com uma conta RH que tem colaborador vinculado:
  - aprovar as próprias férias, ausência e documento retorna acesso negado e gera o evento consultável em `auditoria GET`;
  - um Gestor aprovando a própria correção de ponto é negado;
  - decidir solicitações de outro colaborador continua funcionando.
  - Parcial em 2026-10-06 (código publicado no workspace 147338). Com a conta Admin (colaborador 2):
    - `ferias/5/aprovar|rejeitar`, `ausencias/8/aprovar` e `documentos/18/aprovar` → 403 "Voce nao pode decidir uma solicitacao propria.";
    - os status continuam inalterados;
    - os 4 eventos `autoaprovacao_bloqueada` (falha) aparecem em `auditoria GET`;
    - as férias 6, de outro colaborador, passam pelo bloqueio e param na validação de status (400), sem alterar dados.

    Falta o cenário do Gestor com a própria correção de ponto (não há conta Gestor de teste) e uma decisão positiva efetivamente aplicada.
- [ ] 1.12 Anonimato da pesquisa de clima (item 1.6 da auditoria, design D5): `perguntas_clima/{id}/responder` grava a participação e incrementa `resposta_clima_agregado`, sem gravar em `resposta_clima`. Também valida pesquisa `ativo`, período, colaborador não desligado e a guarda completa. `pesquisas_clima/{id}/resultados` passa a ler o agregado. Verificar por HTTP:
  - resposta fora do período, de pesquisa inativa ou de colaborador desligado é recusada sem gravar participação;
  - resposta válida incrementa o agregado e nenhuma linha nova aparece em `resposta_clima`;
  - os resultados continuam suprimindo grupos abaixo de `minimo_respostas`.
- [ ] 1.13 Function idempotente para consolidar as linhas legadas de `resposta_clima` em `resposta_clima_agregado`, executada uma vez com `xano function run`. Responder à Open Question do `design.md` sobre dados reais. Verificar: a soma das quantidades no agregado é igual ao total de linhas legadas por pergunta, e uma segunda execução não altera nada.
- [ ] 1.14 Troca de e-mail de conta (item 1.7 da auditoria, design D9): `usuarios/{id} PATCH` passa a enfileirar no `email_outbox` um alerta para o e-mail anterior e a auditar os valores anterior e novo. Verificar por HTTP: a troca de e-mail de uma conta de teste gera a linha no outbox para o endereço antigo e o evento de auditoria.
- [ ] 1.15 Swagger (item 1.7 da auditoria, design D9): regenerar os tokens de swagger de todos os grupos no Xano e desativar o swagger público. Fazer `pull` para atualizar os `api/*/conecta_rh_*.xs`. Verificar: os tokens antigos do histórico do git não abrem mais a documentação (teste no navegador) e o diff pós-pull mostra os tokens novos ou o swagger desativado.
- [ ] 1.16 Documentar em `docs/regras-de-negocio.md`:
  - as regras novas da Parte 1 (guarda de acesso, sessão no token, reenvio de OTP, autoaprovação, troca de e-mail e swagger);
  - a reescrita da seção 11.6 (anonimato por agregação);
  - o risco aceito do bloqueio por senha errada (D9).

  Verificar: cada regra cita o endpoint correspondente, e a seção 2.6 e a 11.6 não contradizem o código.
- [ ] 1.17 Registrar as evidências da Parte 1 em `docs/evidencias/seguranca.md`, com o cenário, a requisição (sem token completo) e o resultado esperado e obtido de cada verificação das tarefas 1.4 a 1.15. Verificar: o arquivo não contém e-mail, CPF nem token reais.

## 2. Requisitos da spec não cumpridos (Parte 2)

- [ ] 2.1 Gestor decide férias (item 2.1 da auditoria, design D6): `ferias/{id}/aprovar|rejeitar` aceitam RH/Admin e o Gestor do departamento do colaborador. Verificar por HTTP: o Gestor aprova férias da própria equipe, recebe acesso negado para outro departamento e não consegue aprovar as próprias férias.
- [ ] 2.2 Delegação vigente (item 2.2 da auditoria, design D6) em `ferias/{id}/aprovar|rejeitar` e `correcoes_ponto/{id}/aprovar|rejeitar`. A auditoria registra o titular. Verificar por HTTP: o substituto decide durante a vigência; depois do cancelamento, ou com `data_fim` passada, é negado; uma delegação com escopo incompatível é ignorada.
- [ ] 2.3 Gestor nas ausências (item 2.1 da auditoria): conferir que nenhuma resposta acessível ao Gestor (`calendario`, `central_de_tarefas` e `minha_equipe`) inclui documento, atestado ou observação clínica da ausência. Verificar: inspeção do `output` de cada endpoint e uma chamada HTTP com conta Gestor.
- [ ] 2.4 Criar `rotinas/processar_diarias POST` (item 2.3 da auditoria, design D7), com as 6 transições na ordem do design, idempotente e auditado com contagens. Verificar por HTTP com dados sintéticos de cada caso:
  - todas as transições são aplicadas;
  - a segunda execução retorna contagens zeradas;
  - um colaborador `Desligado` não é reativado;
  - Gestor e Colaborador são negados.
- [ ] 2.5 Estender `status_operacional GET` com a contagem pendente de cada transição da rotina diária. Verificar: os números batem com o que a rotina aplica logo em seguida.
- [ ] 2.6 Criar `ciclos_avaliacao/{id}/status PATCH`, aceitando só as transições válidas e auditado. `metas POST` e `avaliacoes POST` passam a exigir ciclo `em_andamento`. Verificar por HTTP: `planejamento → concluido` é rejeitado, a sequência válida é aceita e criar uma meta em ciclo `planejamento` é rejeitado.
- [ ] 2.7 Criar `pesquisas_clima/{id}/encerrar POST` (RH/Admin, auditado). Verificar: depois de encerrar, `perguntas_clima/{id}/responder` recusa novas respostas.
- [ ] 2.8 Em `onboarding_item/{id}/concluir`, concluir o onboarding quando não restar nenhum item pendente. Verificar por HTTP: concluir o último item muda `onboarding.status` para `concluido`, e concluir um item intermediário não muda.
- [ ] 2.9 Em `organograma GET` e `colaboradores/aniversariantes GET` (item 2.4 da auditoria), trocar o filtro para `status != "Desligado"`. Verificar por HTTP: um colaborador com status `Ferias` aparece nos dois, e um `Desligado` não aparece.
- [ ] 2.10 Criar `minha_equipe GET` (item 2.5 da auditoria, design D8): só Gestor, escopo do departamento, `output` explícito sem CPF, salário, dados bancários nem contato. Verificar por HTTP: o Gestor recebe só a própria equipe sem campos sensíveis, e RH, Admin e Colaborador são negados.
- [ ] 2.11 Completar o dashboard do gestor em `central_de_tarefas` com as avaliações pendentes da equipe, reaproveitando as consultas já existentes. Verificar: os campos do cenário "Dashboard do gestor" da spec aparecem na resposta para uma conta Gestor.
- [ ] 2.12 Deixar `task/concluir_desligamentos_agendados.xs` com `active = false` (item 2.6 da auditoria) e documentar no cabeçalho do arquivo que ele é backlog até o upgrade do plano. Verificar: o dry-run completo não mostra operação pendente para a task.
- [ ] 2.13 Retenção (item 2.7 da auditoria, design D10): `documentos POST` preenche `retencao_ate` a partir de `documento_obrigatorio_regra` quando houver regra aplicável. Criar `documentos/retencao_vencida GET` (RH/Admin, só leitura). Verificar por HTTP: um documento com regra de retenção recebe a data, e a listagem mostra os vencidos sem alterar nenhum.
- [ ] 2.14 Backup (item 2.7 da auditoria, design D10): documentar em `docs/monitoramento.md` o procedimento (`xano workspace pull` versionado mais a exportação de dados) e executar uma restauração num workspace de teste. Verificar: o resultado da restauração fica registrado em `docs/evidencias/backup.md`.
- [ ] 2.15 Registrar no `design.md` do `conectarh.gestao` as decisões da Parte 2: Gestor decide férias, delegação por vigência, rotina diária manual, ciclo de avaliação, versionamento pelo grupo de API, rastreamento no backlog, backup e retenção. Atualizar `docs/regras-de-negocio.md` (seções de férias, ponto, delegação, avaliação, onboarding, documentos e organograma). Verificar: nenhuma regra do documento contradiz os endpoints alterados nas tarefas 2.1 a 2.13.
- [ ] 2.16 Registrar as evidências da Parte 2 em `docs/evidencias/rotinas-e-fluxos.md`. Verificar: há um cenário por tarefa de 2.1 a 2.13, sem dados pessoais.

## 3. Documentação desatualizada ou contraditória (Parte 3)

- [ ] 3.1 No `tasks.md` do `conectarh.gestao`:
  - trocar SendGrid e `SENDGRID_API_KEY` por Brevo e `BREVO_API_KEY` nas tarefas 2.3, 3.2, 4.5, 5.3, 5.4, 5.5 e 5.6;
  - corrigir a nota "todos os 62 endpoints" da 2.3 para refletir a auditoria e a tarefa 1.8 desta change;
  - remover `/api/v1/` da 7.10;
  - reabrir a 4.6, com nota apontando para a tarefa 2.2 desta change.

  Verificar: `grep -i sendgrid` no arquivo não retorna nada, e a 4.6 está `[ ]`.
- [ ] 3.2 Marcar de novo a 4.6 do `conectarh.gestao` como concluída, com referência à tarefa 2.2 desta change, depois que a 2.2 estiver concluída. Verificar: a nota da 4.6 não descreve mais o gap de integração com os endpoints de aprovação.
- [ ] 3.3 Em `docs/figma-prototipo.md`, trocar a seção "Handoff para Reflex" por "Handoff para Streamlit", com as regras da Parte 4 e o link oficial do protótipo. Verificar: `grep -i reflex` no arquivo não retorna nada, e o link abre o arquivo `fph1M5tB4rA4gqfIysSmkn`.
- [ ] 3.4 No `design.md` do `conectarh.gestao`:
  - atualizar a contagem de endpoints para 178;
  - remover a afirmação "nenhum endpoint aceita uma requisição fora do escopo autorizado";
  - depois da tarefa 1.8, substituir essa afirmação pela garantia verificada pelo `tools/checar_endpoints.py`.

  Verificar: a contagem bate com `find xano-workspace/api -name "*.xs"`, sem contar os arquivos de grupo.
- [ ] 3.5 Em `docs/domain-model.md`, remover a frase que diz que RegraContrato e RegraAplicada não têm endpoint, citando `resolver_regra` e `regras_override/aplicar`. Verificar: a seção "RegraContrato / RegraAplicada" bate com o código.
- [ ] 3.6 Atualizar o README (design D11): explicar que os grupos refletem a ordem histórica de criação, incluir a tabela de domínio por grupo de API e remover "organizados por domínio". Verificar: cada um dos 10 grupos aparece na tabela com seus módulos.
- [ ] 3.7 Criar `docs/evidencias/`, versionada, com um `README.md` de regras (sem dados pessoais, mascaramento de e-mail e token). Migrar o conteúdo não sensível de `docs/testes-integracao.md`, `docs/testes-seguranca.md` e `docs/auditoria.md`. Ajustar a tarefa 7.6 do `conectarh.gestao` para apontar para essa pasta. Verificar: `git status` mostra `docs/evidencias/` rastreada, e `grep -E "@|Bearer "` na pasta não encontra dado real.
- [ ] 3.8 Remover do workspace e do Xano `function/getting_started_template/*` e `ai/agent`, que são exemplos do Xano sem uso. Verificar: `grep` não encontra referência a eles em `api/` nem em `function/conectahr/`; o dry-run com `--sync --delete` lista só esses itens, e o diff pós-pull está limpo.

## 4. Frontend segue o protótipo do Figma (Parte 4)

- [ ] 4.1 No `design.md` do `implementar-frontend-streamlit`, registrar a decisão "Protótipo Figma como fonte única", com o link oficial e as 7 regras do design D13 desta change. Verificar: o link e as regras aparecem numa decisão própria do documento.
- [ ] 4.2 Conferir no Figma quais destas telas existem: troca de senha no primeiro acesso, logout e expiração do token, organograma, comunicados e FAQ, solicitações ao RH, pesquisa de clima, indicadores, gestão de usuários, cargos, departamentos e colaboradores, desligamento, delegações, sessões, notificações e preferências, calendário, minha equipe e dashboard do gestor. Registrar a lista das que faltam como pendência no `design.md` do frontend. Verificar: cada tela aparece com o nó do Figma ou com a marcação "a desenhar".
- [ ] 4.3 Adicionar ao `tasks.md` do `implementar-frontend-streamlit` uma seção por tela da 4.2, no ciclo "conferir no Figma (desenhar antes, se faltar) → construir → integrar → testar". A troca de senha no primeiro acesso e a expiração do token entram como prioridade. Verificar: `openspec status --change implementar-frontend-streamlit` mostra as tarefas novas, e cada tela tem uma tarefa de conferência no Figma.
- [ ] 4.4 Adicionar ao spec do `implementar-frontend-streamlit` o cenário de tela para a troca de senha no primeiro acesso e a sessão revogada (o usuário volta para "Entrar" com mensagem). Verificar: `openspec validate implementar-frontend-streamlit` passa.

## 5. Instruções para agentes de IA (Parte 5)

- [ ] 5.1 Reescrever o `AGENTS.md` da raiz como fonte única, com:
  - visão e perfis;
  - fora de escopo;
  - stack e pastas;
  - fluxo OpenSpec → branch `feature/CON-XX-descricao` → commit `CON-XX` → PR com revisão, sem push direto no `master`;
  - checklist de endpoint do Xano;
  - regras do frontend com o link do Figma;
  - segredos;
  - testes contra o Xano real e evidências em `docs/evidencias/`;
  - idioma pt-BR;
  - configuração do MCP do Figma no Codex, no Gemini CLI e no Claude, com o Dev Mode como alternativa.

  Verificar: cada item da Parte 5.1 e da 5.4 do pedido tem uma seção correspondente.
- [ ] 5.2 Criar `frontend/AGENTS.md`, com:
  - as regras da Parte 4;
  - como rodar (venv, `requirements.txt`, `secrets.toml` de exemplo sem valores reais);
  - o padrão do `api_client.py`;
  - o uso obrigatório de `theme.py` e de `st.html()`;
  - os 6 estados de UI.

  O arquivo remete ao `AGENTS.md` da raiz. Verificar: seguir as instruções de execução num clone limpo sobe o Streamlit.
- [ ] 5.3 Criar `xano-workspace/AGENTS.md`, com:
  - o checklist de endpoint;
  - os padrões de XanoScript adotados (precondition, "registra e depois falha", auditoria inline, outbox de e-mail e rotina manual);
  - o fluxo de publicação (`push --dry-run` → push → `pull` e diff);
  - o uso do `tools/checar_endpoints.py`.

  Verificar: o checklist é igual ao da raiz e ao que o script confere.
- [ ] 5.4 Criar `.gemini/settings.json` com `{"contextFileName": "AGENTS.md"}`. Criar `GEMINI.md` e `CLAUDE.md` na raiz, cada um com a instrução única "Siga integralmente o AGENTS.md deste repositório." Conferir que `.agents/`, `skills-lock.json` e `.claude/scheduled_tasks.lock` continuam no `.gitignore`. Verificar: `git status` mostra os 3 arquivos novos rastreados e nenhum arquivo pessoal.
- [ ] 5.5 Com Codex, Gemini CLI e Claude Code, abrir o repositório e perguntar "Quais são as regras para criar um endpoint e uma tela neste projeto?". Verificar: as três respostas citam o checklist de endpoint e o link do Figma. Registrar as respostas resumidas em `docs/evidencias/agentes.md`.

## 6. Integração final

- [ ] 6.1 Rodar `tools/checar_endpoints.py` em todo o workspace e um smoke test HTTP por perfil (Admin, RH, Gestor e Colaborador), cobrindo login, um endpoint de leitura e um de decisão de cada módulo alterado. Verificar: zero falhas no script, resultado esperado em todas as chamadas e registro em `docs/evidencias/`.
- [ ] 6.2 Rodar `openspec validate corrigir-brechas-e-alinhar-documentacao` e conferir que o arquivamento desta change fica depois do `conectarh.gestao` e do `implementar-frontend-streamlit` (design, Migration Plan). Verificar: a validação passa sem erros.
