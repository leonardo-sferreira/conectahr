# Design

## Context

A motivação está em `proposal.md`. Os requisitos estão no delta `specs/conectahr/spec.md`. Este documento registra apenas as restrições que definem como a correção será feita:

- **Autorização replicada.** A autorização é feita endpoint a endpoint, sem function ou middleware compartilhado (decisão registrada no `design.md` do `conectarh.gestao`, seção "Autorizacao"). O motivo é que, neste workspace, chamar uma function a partir de outra não é confiável e chamar uma function a partir de uma query nunca foi confirmado em execução. Qualquer guarda nova precisa, portanto, ser replicada inline nos 173 endpoints autenticados.
- **Sem tarefas agendadas.** O plano do Xano não oferece Background Tasks. O padrão já adotado é o endpoint acionado manualmente pelo RH (`documentos/processar_vencimentos`, `email_outbox/processar`, `pendencias_atrasadas/escalonar`).
- **Token sem vínculo com sessão.** O token é emitido em `auth/otp/validar` com `extras = {perfil}` e não guarda referência à sessão. A tabela `sessao` (`ativa`, `revogada_em`, `expira_em`) existe, mas nenhum endpoint de negócio a consulta. A leitura de `extras` por meio de `$auth` nunca foi testada neste workspace (gap registrado na tarefa 2.2 do `conectarh.gestao`).
- **Correlação na pesquisa de clima.** `resposta_clima` e `resposta_clima_participacao` são gravadas na mesma requisição. As duas usam id autoincremental e `created_at` com precisão de milissegundos, o que permite cruzar participação e resposta.
- **Capability sem spec principal.** A capability `conectahr` ainda não existe em `openspec/specs/`. Ela é criada pelos changes `conectarh.gestao` e `implementar-frontend-streamlit`.

## Goals / Non-Goals

**Goals:**
- Fazer com que a guarda de acesso (usuário ativo, senha trocada e sessão válida) seja uma propriedade verificável de todo endpoint autenticado, conferida por script e não apenas por leitura.
- Fechar as brechas usando os padrões do código que já existem: `precondition`, a sequência "registra e depois falha" para auditar recusas, outbox de e-mail e rotina manual.
- Deixar a documentação igual ao comportamento real do sistema, com um único ponto de verdade para pessoas e agentes de IA.

**Non-Goals:**
- Centralizar a autorização numa function ou middleware. Isso continua como débito técnico.
- Reorganizar os grupos de API ou mudar URLs base.
- Aplicar a delegação a escopos além de `ferias` e `correcao_ponto`.

## Decisions

### D1. Guarda de acesso replicada inline, conferida por script

Todo endpoint com `auth = "user"` segue este bloco, nesta ordem, no topo do `stack`:

1. `db.get user` pelo `$auth.id`;
2. `precondition` de usuário existente;
3. `precondition ($usuario.ativo)`;
4. `precondition ($usuario.senha_primeiro_acesso == false)`, exceto em `auth/senha PATCH`, `auth/me`, `auth/logout`, `auth/minhas_sessoes`, `auth/sessoes/{id}/encerrar` e `auth/sessoes/encerrar_outras`;
5. validação da sessão (D2).

As mensagens seguem as que já existem: "Usuario inativo." e "Troque a senha temporaria antes de continuar."

Para não depender de revisão manual em 173 arquivos, será criado o script `tools/checar_endpoints.py`, em Python, linguagem que o projeto já usa no frontend. O script lê cada `.xs` de `xano-workspace/api/`, identifica os endpoints autenticados e falha quando falta alguma das guardas. Ele vira o critério de verificação das tarefas da Parte 1 e o item do checklist do `xano-workspace/AGENTS.md`.

- **Alternativa: function compartilhada `validar_acesso`.** Rejeitada pelas falhas já conhecidas em chamadas de function (ver Context).
- **Alternativa: middleware do Xano por grupo de API.** Rejeitada porque não existe forma testada de declará-lo em XanoScript textual. Fica registrada como evolução futura.

### D2. Sessão vinculada ao token

Em `auth/otp/validar`, a ordem passa a ser:

1. criar o registro em `sessao`;
2. emitir o token com `extras = {perfil, sessao_id}`.

Cada endpoint autenticado então carrega a sessão pelo `$auth.extras.sessao_id` (ou pelo acessor que o spike confirmar) e exige `ativa == true`, `revogada_em == null`, `expira_em > now` e `sessao.user_id == $auth.id`.

O comportamento dos endpoints de sessão fica assim:

- **Logout:** encerra a sessão do token.
- **`encerrar_outras`:** encerra todas as sessões, menos a do token.
- **`sessoes/{id}/encerrar`:** encerra a sessão indicada, desde que pertença ao usuário.
- **`usuarios/{id}/status PATCH`**, quando desativa, e conclusão de desligamento (imediato, `concluir` e rotina diária): revogam todas as sessões do usuário.

Tokens emitidos antes da mudança não têm `sessao_id` e passam a ser recusados. O impacto é aceitável, porque os tokens valem 1 h e basta fazer login de novo.

**Spike obrigatório antes do retrofit (tarefa 1.1):** emitir um token com `sessao_id` e ler o valor num endpoint de teste. Se não houver acessor confiável, a alternativa é gravar em `sessao` um hash do token e comparar na requisição, desde que a requisição dê acesso ao token bruto. Para o hash, `|md5` funciona neste workspace; `sha256` não. Se nenhuma das duas funcionar, a Parte 1.3 para e este design é revisto antes de seguir. As 1.1 e 1.2 não dependem do spike.

### D3. Reenvio de OTP

Campos novos em `user`, sem remover nenhum: `otp_reenvios` (int) e `otp_ultimo_envio_em` (timestamp). As regras ficam assim:

- **`auth/login`:** zera `otp_reenvios` e grava `otp_ultimo_envio_em`.
- **`auth/otp/reenviar`:**
  - exige `otp_tentativas < 5`, `otp_reenvios < 3` e `now - otp_ultimo_envio_em >= 60 s`;
  - não zera `otp_tentativas`;
  - incrementa `otp_reenvios`;
  - mantém a mensagem genérica.
- **`auth/otp/validar`:** na 5ª tentativa errada, grava `otp_codigo = null`.

O limite de 3 reenvios é uma suposição desta change. A spec original não define o número, e o valor pode ser ajustado sem mudar a abordagem.

### D4. Bloqueio de autoaprovação

Em cada endpoint de decisão, depois de carregar a solicitação e antes de qualquer escrita, é feita uma comparação. Se o `colaborador.user_id` da solicitação for igual a `$auth.id`, o endpoint grava uma auditoria (`acao: "autoaprovacao_bloqueada"`, `resultado: "falha"`) e depois executa `precondition (false)` com `accessdenied`. É a mesma sequência "registra e depois falha" de `auth/otp/validar`, em que a escrita feita antes do erro é mantida, como confirmado pelo contador de tentativas.

Endpoints cobertos:

- `ferias/{id}/aprovar|rejeitar`
- `ausencias/{id}/aprovar|rejeitar|registrar`
- `correcoes_ponto/{id}/aprovar|rejeitar`
- `documentos/{id}/aprovar|rejeitar`
- `solicitacoes_desligamento/{id}/iniciar_analise|aprovar|rejeitar|concluir`
- `solicitacoes/{id}/atender|indeferir`
- `contestacoes_avaliacao/{id}/revisar`

Instrumentos normativos e `regras_override` já bloqueiam a autoaprovação pelo autor e não mudam.

### D5. Anonimato da pesquisa de clima por agregação

A nova tabela `resposta_clima_agregado` tem os campos `pergunta_clima_id`, `departamento_id`, `nota`, `quantidade` e índice único nos três primeiros. Ela não tem `created_at` nem `updated_at`. Ao responder, o endpoint:

1. grava a participação;
2. incrementa `quantidade` na linha `(pergunta, departamento, nota)`, criando a linha se ela não existir.

Não existe mais registro individual de resposta, portanto não há id nem horário que permita a correlação. `pesquisas_clima/{id}/resultados` passa a somar as quantidades e mantém a supressão abaixo de `minimo_respostas`.

`resposta_clima` deixa de receber gravações e de ser lida. A tabela não é removida, para evitar migração destrutiva. As linhas existentes são consolidadas no agregado por uma function idempotente executada uma única vez.

`resposta_clima_participacao` continua a existir só para impedir resposta duplicada. Seu `created_at` deixa de ter importância, porque não existe registro individual para cruzar.

Validações novas em `perguntas_clima/{id}/responder`:

- `pesquisa.ativo`;
- `data_inicio <= hoje <= data_fim`;
- colaborador com status diferente de `Desligado`;
- guarda de acesso completa (D1).

Novo endpoint `pesquisas_clima/{id}/encerrar POST`, para RH e Admin: grava `ativo = false` e audita.

- **Alternativa: truncar `created_at` para o dia.** Rejeitada porque a ordem dos ids continuaria permitindo a correlação.

### D6. Gestor decide férias e uso da delegação

`ferias/{id}/aprovar|rejeitar` passam a reproduzir o escopo de `correcoes_ponto/{id}/aprovar`: RH e Admin podem decidir qualquer solicitação; o Gestor, só se `departamento.gestor_colaborador_id` for o seu colaborador. A esse escopo se soma o substituto.

O substituto é aceito quando existe uma `delegacao_aprovacao` que atende a todas as condições:

- `substituto_user_id == $auth.id`;
- `escopo` igual ao tipo da decisão (`ferias` ou `correcao_ponto`) ou `todas`;
- `data_inicio <= hoje <= data_fim`;
- `cancelada_em == null`;
- o titular é o Gestor do departamento do colaborador.

A auditoria da decisão registra `titular_user_id` na justificativa. O mesmo bloco é aplicado em `correcoes_ponto/{id}/aprovar|rejeitar`. A expiração continua sendo calculada pela vigência na leitura.

Os demais escopos do enum (ausência, documento, desligamento e `solicitacao_rh`) ficam no backlog, porque os endpoints correspondentes não dão poder de decisão ao Gestor.

Nas ausências, os endpoints de consulta usados pelo Gestor (`minha_equipe` e o calendário) retornam só tipo, período e status, nunca `documento`, `atestado` ou observação.

### D7. Rotina diária manual

`rotinas/processar_diarias POST`, para RH e Admin, executa em sequência as seis transições da spec:

1. férias `Aprovada` com data final passada viram `Concluida`;
2. o status do colaborador muda para `Ferias` ou volta para `Ativo`;
3. o status do colaborador muda para `Afastado` ou volta para `Ativo`;
4. ponto `Aberto` de dias anteriores vira `Incompleto`;
5. instrumento `vigente` com vigência encerrada vira `expirado`;
6. desligamento agendado com data efetiva já atingida é concluído.

A idempotência vem do filtro de cada consulta, que seleciona só os registros ainda no estado de origem. Uma nova execução não encontra nada para mudar.

A ordem importa: primeiro os desligamentos, depois os status. Assim, quem acabou de ser desligado não volta a `Ativo`. A volta para `Ativo` exige que não exista outro afastamento ou outras férias vigentes.

A conclusão de desligamento reproduz a transação de `solicitacoes_desligamento/{id}/concluir`, com histórico profissional e revogação de sessões. A rotina grava um evento de auditoria com as contagens.

`status_operacional GET` passa a mostrar quantos itens cada transição aplicaria agora.

`task/concluir_desligamentos_agendados.xs` fica com `active = false` e é documentado como backlog até um eventual upgrade do plano.

### D8. Ciclo de avaliação, onboarding, organograma e minha equipe

- **`ciclos_avaliacao/{id}/status PATCH`:** usa uma tabela de transições válidas declarada como `var` no topo do stack. É o mesmo padrão de `catalogos`, para evitar o problema já conhecido do literal de array em `response`. O endpoint é auditado. `metas POST` e `avaliacoes POST` passam a exigir ciclo `em_andamento`.
- **`onboarding_item/{id}/concluir`:** depois de concluir um item, conta os itens não concluídos. Se a contagem for zero, grava `onboarding.status = "concluido"`.
- **`organograma` e `aniversariantes`:** o filtro passa de `status == "Ativo"` para `status != "Desligado"`.
- **`minha_equipe GET`:** só para Gestor, com `output` explícito sem CPF, salário, dados bancários nem contato. Reaproveita as consultas do dashboard do gestor em `central_de_tarefas`, que também é completado com as avaliações pendentes da equipe. `colaboradores/{id} GET` continua restrito a RH e Admin.

### D9. Riscos menores (Parte 1.7)

- **Troca de e-mail.** Escolhido o alerta ao e-mail antigo, enviado pelo `email_outbox`, mais a auditoria com o valor anterior e o novo. A alternativa, exigir confirmação no e-mail antigo antes de aplicar, foi rejeitada por exigir um novo fluxo de token de confirmação, além de um e-mail antigo que pode já não existir (caso comum quando o RH corrige um e-mail errado).
- **Swagger.**
  - Regenerar os tokens de swagger de todos os grupos no Xano.
  - Desativar o swagger público dos grupos, se a opção existir no XanoScript. Se não existir, desativar pela interface.
  - Os tokens antigos que estão no histórico do git ficam inválidos. Não haverá reescrita do histórico, que seria destrutiva para os clones do grupo.
  - Registrar a decisão em `docs/regras-de-negocio.md`, seção de segurança.
- **Bloqueio por senha errada.** O risco de bloqueio direcionado (15 min) fica documentado como aceito no MVP: o impacto se limita à disponibilidade, o bloqueio é temporário e as tentativas são auditadas. O limite por IP vai para o backlog, porque o Xano não expõe, de forma confiável e testada neste workspace, o IP real do cliente atrás do proxy.

### D10. Lacunas registradas como decisão (Parte 2.7)

- **Versionamento:** feito pela URL base do grupo de API do Xano. A exigência de `/api/v1/` sai da tarefa 7.10 do `conectarh.gestao`.
- **Identificador de rastreamento por requisição:** fica no backlog.
- **Backup:** o procedimento é `xano workspace pull` versionado no git, mais a exportação dos dados de cada tabela pela interface do Xano. Deve ser testado uma vez com restauração num workspace de teste, com o resultado registrado em `docs/evidencias/`.
- **Retenção:** campo novo `documento.retencao_ate` (date, opcional), preenchido na criação a partir de `documento_obrigatorio_regra` quando houver regra aplicável. Nova listagem `documentos/retencao_vencida GET`, para RH e Admin. Não há eliminação automática no MVP.

### D11. Grupos de API: documentar, não reorganizar

Os grupos ficam como estão, sem renomear e sem mover endpoints. Mover endpoints muda a URL base que o frontend já consome (`.streamlit/secrets.toml`) e invalida as evidências de teste no meio da construção do frontend. Renomear exige alterar `api_group = "..."` em cerca de 178 arquivos, e o único ganho seria cosmético.

O README passa a explicar que os grupos refletem a ordem histórica de criação, não o domínio. Também passa a trazer uma tabela de domínio por grupo e a dizer qual grupo contém cada módulo (avaliação, clima, FAQ, regras, indicadores e auditoria estão em "ConectaRH — Colaboradores").

A reorganização fica no backlog, para ser feita depois da entrega.

### D12. Evidências versionadas

As evidências ficam em `docs/evidencias/`, uma pasta versionada, com um arquivo por área (autenticação, autorização, segurança e rotinas) e sem dados pessoais. Usuários de teste aparecem por perfil ("conta RH de teste") e e-mails e tokens são mascarados.

`docs/testes-integracao.md`, `docs/testes-seguranca.md` e `docs/auditoria.md` continuam locais. O conteúdo sem dados pessoais é migrado para `docs/evidencias/`, para cumprir a tarefa 7.6.

### D13. Regras do frontend (Parte 4)

O requisito "Protótipo Figma como fonte única do frontend" e as regras de tela passam a ser registrados em quatro lugares, com o link oficial do protótipo:

- `design.md` do `implementar-frontend-streamlit`;
- `docs/figma-prototipo.md`, que troca a seção "Handoff para Reflex" por "Handoff para Streamlit";
- `AGENTS.md`;
- `frontend/AGENTS.md`.

As regras são:

1. ler o nó no Figma, pelo MCP ou pelo Dev Mode, antes de codar;
2. não criar nada visual fora dos tokens e componentes de `theme.py`;
3. tela inexistente no Figma deve ser desenhada primeiro;
4. textos idênticos aos do protótipo;
5. os 6 estados de UI devem seguir o Figma;
6. o PR deve trazer o link do nó e os prints lado a lado;
7. o menu por perfil é só conveniência.

As 13 telas que faltam viram tarefas no ciclo "conferir no Figma → construir → integrar → testar" do `tasks.md` daquele change.

Este change só registra as regras e o plano. A construção das telas pertence ao `implementar-frontend-streamlit`.

### D14. Instruções para agentes (Parte 5)

O `AGENTS.md` da raiz é a fonte única.

- O Codex lê o `AGENTS.md` nativamente.
- O Gemini CLI é apontado para ele por `.gemini/settings.json` (`{"contextFileName": "AGENTS.md"}`) e por um `GEMINI.md` de uma linha.
- O Claude Code é apontado por um `CLAUDE.md` de uma linha.

Arquivos por pasta (`frontend/AGENTS.md` e `xano-workspace/AGENTS.md`) trazem só o que é específico daquela pasta e remetem ao da raiz, para não haver duas versões da mesma regra.

`.gemini/settings.json`, `GEMINI.md` e `CLAUDE.md` são versionados. `.agents/`, `skills-lock.json` e `.claude/scheduled_tasks.lock` continuam no `.gitignore`.

### D15. Convenção de branches e commits

- **Branch:** `feature/CON-XX-descricao`.
- **Commit:** `CON-XX <descrição> (<tarefa>)`.
- **PR:** `CON-XX` no título.

Os números `CON-XX` vêm dos cards do Jira criados para cada tarefa desta change, um card por grupo de tarefas, no mínimo. O `tasks.md` não fixa os números, que são definidos ao abrir o card.

## Risks / Trade-offs

- [O retrofit em 173 arquivos pode quebrar endpoints que já funcionam] → Uma tarefa por grupo de API. `tools/checar_endpoints.py` roda antes de cada push. Primeiro `xano workspace push --dry-run`, depois o push real e o diff com `pull`. Depois de cada grupo, um smoke test HTTP com um endpoint por perfil.
- [O acessor de `extras` no `$auth` pode não existir] → Spike na tarefa 1.1, com alternativa por hash do token. Se as duas falharem, a 1.3 é suspensa e o design é revisto. As 1.1 e 1.2 seguem.
- [Tokens emitidos antes do deploy passam a ser recusados] → Duram no máximo 1 h. Avisar o grupo antes do push e fazer o push fora do horário de testes.
- [A guarda de primeiro acesso pode prender o frontend atual] → A tela de troca de senha no primeiro acesso entra como prioridade no `tasks.md` do frontend (Parte 4.3). Até ela existir, a troca pode ser feita pela API.
- [Corrida no incremento do agregado da pesquisa de clima] → O volume é baixo e o índice único impede linha duplicada. Uma perda pontual de incremento em respostas simultâneas é aceita e documentada.
- [Respostas legadas em `resposta_clima` continuam correlacionáveis] → Elas ficam sem leitura por endpoint. Ver Open Questions.
- [A rotina diária depende de alguém acionar] → `status_operacional` mostra o que está pendente. Também é o mesmo padrão já aceito para vencimentos e outbox.

## Migration Plan

1. Schema aditivo, com push isolado:
   - `user.otp_reenvios` e `user.otp_ultimo_envio_em`;
   - `documento.retencao_ate`;
   - tabela `resposta_clima_agregado`.
2. Spike de sessão (1.1). Depois, `auth/otp/validar` passa a emitir `sessao_id`.
3. Retrofit da guarda (D1 e D2), grupo a grupo, com checagem por script e smoke test.
4. Correções e endpoints novos das Partes 1.4 a 2.6.
5. Consolidação das respostas legadas da pesquisa de clima (function idempotente executada uma vez).
6. Documentação e arquivos de agentes (Partes 3 a 5).

**Rollback:** cada grupo é um commit e um push separados. Para desfazer, basta reverter o commit e repetir o `xano workspace push` dos arquivos do grupo. Os campos e tabelas novos são aditivos e podem ficar no schema mesmo depois de um rollback de código.

**Ordem de arquivamento:** `conectarh.gestao` → `implementar-frontend-streamlit` → esta change.

## Open Questions

- Existem respostas reais (não de teste) em `resposta_clima`? Se não existirem, nada muda. Se existirem, a equipe decide entre aceitar o risco residual nas linhas legadas ou anonimizá-las (substituir `departamento_id` por nulo, por exemplo), sem exclusão física. A decisão não muda a abordagem nem as tarefas: a consolidação no agregado acontece nos dois casos.
- Qual é a sintaxe exata para desativar o swagger público no XanoScript? Se não existir, a desativação é feita pela interface. Em qualquer caso, a tarefa é a mesma.
