# Proposal

## Why

Uma auditoria cruzou o backend Xano (`xano-workspace/`, 178 endpoints e 48 tabelas), a spec e os artefatos do change `conectarh.gestao`, os documentos em `docs/` e o frontend da branch `feature/frontend-login`. Ela encontrou quatro grupos de problemas:

1. Brechas de segurança que não estão documentadas. Por exemplo: o primeiro acesso não bloqueia o sistema, usuários inativos continuam operando, o logout não revoga o token, o reenvio de código burla o limite de tentativas, RH, Admin e Gestor conseguem aprovar a própria solicitação e a pesquisa de clima não é realmente anônima.
2. Requisitos da spec que o código não cumpre: o Gestor não decide férias, a delegação não é usada, as transições de status por data não existem e o organograma esconde quem está de férias.
3. Documentos que se contradizem: menções a SendGrid e Reflex, contagens de endpoints desatualizadas e a afirmação de que "nenhum endpoint aceita requisição fora do escopo".
4. Falta de regras únicas para o frontend e para os agentes de IA que o grupo usa (Codex, Gemini e Claude).

Hoje o projeto declara garantias que o código não entrega. Isso precisa ser corrigido antes de o frontend ser integrado e antes da entrega final (tarefa 7.6 do `conectarh.gestao`).

## What Changes

**Parte 1: brechas de segurança (código do backend)**
- Todo endpoint autenticado passa a recusar usuário inativo, usuário com senha temporária e token de sessão encerrada ou expirada. As únicas exceções à regra da senha temporária são `auth/senha PATCH`, `auth/me`, `auth/logout` e as rotas de sessão. **BREAKING:** clientes que hoje usam um token de usuário com senha temporária para operar os módulos passam a receber acesso negado.
- O token passa a carregar o id da sessão. Logout e encerramento de sessão revogam exatamente a sessão do token. A desativação do usuário e a conclusão do desligamento revogam todas as sessões dele.
- `auth/otp/reenviar` deixa de zerar as tentativas, fica bloqueado depois de 5 erros, ganha limite de reenvios por código e intervalo mínimo de 60 s. Ao atingir 5 erros, o código é descartado.
- Toda decisão sobre solicitação (aprovar, rejeitar, registrar, atender, indeferir, revisar, concluir) é bloqueada e auditada quando o decisor é o próprio colaborador da solicitação.
- A pesquisa de clima deixa de gravar respostas individuais correlacionáveis com a participação e passa a validar pesquisa ativa, período, status do colaborador e estado do usuário.
- Riscos menores: troca de e-mail de conta pelo RH passa a alertar o e-mail antigo; os tokens de swagger são regenerados; o risco do bloqueio por senha errada é documentado como aceito.

**Parte 2: requisitos da spec não cumpridos**
- O Gestor decide férias no escopo do departamento. Nas ausências, o Gestor só consulta o status, sem acesso ao atestado.
- A delegação vigente passa a valer em férias e correção de ponto. A expiração é feita pela vigência, sem rotina.
- Novo `rotinas/processar_diarias POST` (RH/Admin, manual, idempotente e auditado) para as transições por data: férias concluídas, status Férias/Afastado/Ativo do colaborador, ponto incompleto, instrumento expirado e desligamento agendado.
- Novos `ciclos_avaliacao/{id}/status PATCH` e `pesquisas_clima/{id}/encerrar POST`. Metas e avaliações passam a exigir ciclo `em_andamento`. O onboarding é concluído automaticamente quando todos os itens estão concluídos.
- Organograma e aniversariantes passam a mostrar quem não está desligado.
- Novo `minha_equipe GET` (só Gestor) e dashboard do gestor completo.
- `task/concluir_desligamentos_agendados.xs` fica inativo e registrado como backlog.
- Decisões registradas: versionamento pelo grupo de API (sem `/api/v1/`), identificador de rastreamento no backlog, procedimento de backup testado e campo `retencao_ate` com revisão manual.

**Parte 3: documentação**
- Corrige `tasks.md` e `design.md` do `conectarh.gestao`, `docs/figma-prototipo.md`, `docs/domain-model.md`, `docs/regras-de-negocio.md` e o README (grupos de API).
- Define `docs/evidencias/` como local versionado das evidências de teste, sem dados pessoais.
- Remove do workspace os exemplos `function/getting_started_template/*` e `ai/agent`.

**Parte 4: frontend**
- O protótipo Figma passa a ser a fonte única do frontend Streamlit, com regras obrigatórias por tela.
- As telas que faltam entram no `tasks.md` do `implementar-frontend-streamlit`.

**Parte 5: agentes de IA**
- `AGENTS.md` da raiz vira a referência única. São criados `frontend/AGENTS.md`, `xano-workspace/AGENTS.md`, `GEMINI.md`, `.gemini/settings.json` e `CLAUDE.md` apontando para ele.

**Non-goals**
- Folha de pagamento, certificação de ponto REP-P/REP-A/REP-C e ConectaRH Vagas.
- Upgrade do plano Xano ou qualquer rotina agendada automática.
- Eliminação automática de documentos por retenção.
- Uso da delegação em escopos além de férias e correção de ponto. Os demais ficam no backlog.
- Reorganização dos grupos de API do Xano. Ver `design.md`.
- Exclusão física de dados ou migração destrutiva de schema.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `conectahr`: endurecimento de autenticação, sessão e primeiro acesso; bloqueio de autoaprovação; anonimato e período da pesquisa de clima; decisão de férias pelo Gestor e uso da delegação; transições de status por rotina manual; ciclo de avaliação; organograma e aniversariantes; visão "minha equipe"; retenção com revisão manual; versionamento e rastreamento; protótipo Figma como fonte única do frontend.

  A capability `conectahr` ainda não existe em `openspec/specs/`. Ela é criada pelos changes `conectarh.gestao` e `implementar-frontend-streamlit`, ainda não arquivados. Este change precisa ser arquivado **depois** dos dois.

## Impact

- **Backend Xano:** todos os 173 endpoints autenticados (guarda de acesso), o grupo de autenticação (sessão no token, reenvio de OTP), os endpoints de decisão de férias, ausências, correção de ponto, documentos, desligamento, solicitações ao RH e contestações, além de clima, organograma, aniversariantes, onboarding, metas e avaliações. Novos endpoints: `rotinas/processar_diarias`, `ciclos_avaliacao/{id}/status`, `pesquisas_clima/{id}/encerrar`, `minha_equipe` e a listagem de retenção de documentos. Schema: tabela de agregados da pesquisa de clima e campos novos, sem remover colunas.
- **Frontend:** precisa tratar a troca de senha no primeiro acesso, a sessão revogada e o acesso negado por senha temporária (telas novas no change de frontend).
- **Documentação e OpenSpec:** `conectarh.gestao` (tasks.md e design.md), `implementar-frontend-streamlit` (design.md e tasks.md), `docs/*`, README, `.gitignore` e os novos arquivos de instruções para agentes.
- **Operação:** regenerar os tokens de swagger no Xano e registrar o procedimento de backup e restauração.
- **Processo:** branches, commits e PRs passam a referenciar o card do Jira (`CON-XX`) e o número da tarefa.
