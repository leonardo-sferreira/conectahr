# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil. As evidências vão para `docs/evidencias/sla-de-solicitacoes.md`, sem dado pessoal.

## 1. Tela

- [x] 1.1 Figma, antes de codar, nos temas claro e escuro. Verificar: print dos nós.
  - a aba "SLA de solicitações" em Configurações: a tabela por setor e tipo e o modal de edição (Admin), e a leitura (RH);
  - o selo "Responder até" nas filas, na Central de Pendências e em "Meus pedidos".
  - **Feito (20/11/2026):** seção 5 do Protótipo (claro) e Protótipo — Dark: "Configurações — SLA de solicitações" (Admin, com "Editar"; RH, só leitura), "Modal/Alterar prazo (SLA)" e "Selo/Responder até (SLA)" com os quatro estados. Prints conferidos.
- [x] 1.2 `sla_modelo.py`: a situação, o selo e a ordem (D5, D6). Verificar: regras em `tools/testar_sla.py`.
  - **Feito (20/11/2026):** `tools/testar_sla.py`, parte de regras.
- [x] 1.3 A aba "SLA de solicitações", com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada); o RH só lê e o Gestor não vê a aba (D4, D6). Verificar: `tools/testar_sla.py`.
  - **Feito (20/11/2026):** `frontend/sla_ui.py`; `tools/testar_sla.py` 22/22 (Admin edita e volta ao padrão, RH só lê, Gestor e Colaborador sem a aba, vazio, erro e recusa 403 no modal). O carregando é o spinner padrão.
- [x] 1.4 O selo nas filas (Central de Pendências, Solicitações ao RH, Desligamentos, Férias, Ausências, Folha de ponto e Usuários e perfis) e em "Meus pedidos" (D6). Verificar: os testes de cada tela conferem o selo, e "Sem prazo" nos pedidos antigos.
  - **Feito (20/11/2026):** Central (férias, correções e ausências, em ordem de prazo), Solicitações ao RH, Desligamentos, Ausências, Folha de ponto (pedidos de correção) e Usuários e perfis (pedidos de acesso); em "Meus pedidos" (privacidade e desligamento) o prazo entra como texto. Os 36 passos de teste do CI passam.

## 2. Integrar

- [x] 2.1 A tabela `sla_config` e os campos `prazo_sla`, `alerta_sla`, `sla_horas` e `aviso_sla_em` nas 6 tabelas de pedido (D1, D3). Verificar: dry-run só com `CREATE` e `ADD_FIELD`.
  - **Feito (20/11/2026):** dry-run só com `CREATE` de `sla_config` e `ADD_FIELD` nas 6 tabelas (antes, as tabelas no ar conferidas iguais ao git); publicado.
- [x] 2.2 `ConectaHR/somar_horas_uteis` e `ConectaHR/prazo_sla` (D2, D3). Verificar: os quatro exemplos do D2 (segunda, sexta, sábado e semana com feriado) num endpoint de teste ou na 3.1.
  - **Feito (20/11/2026):** pela CLI (`xano function run`), os exemplos do D2 e dois feriados reais (02/11 e 20/11/2026) batem; o exemplo do sábado no D2 estava errado e foi corrigido (quinta às 00h). Ver `docs/evidencias/sla-de-solicitacoes.md`.
- [x] 2.3 `sla_config` GET, POST e `{id}` PATCH, só Admin para gravar, com auditoria (D4). Verificar: `checar_endpoints` e a 3.2.
  - **Feito (20/11/2026):** publicados; `checar_endpoints` sem falha; a 3.2 passou.
- [x] 2.4 O POST de cada tipo grava o prazo, com o teto legal no pedido LGPD; as listagens e a `central_de_tarefas` devolvem prazo e situação, em ordem (D3, D5). Verificar: a 3.1 e a 3.3.
  - **Feito (20/11/2026):** os 6 POST de pedido (o `folha_ponto/tratar` fica de fora: o ajuste direto do RH já nasce aprovado), `ausencias` e `minhas_ausencias` GET, `solicitacoes_acesso` GET e a `central_de_tarefas` (ordem pelo prazo). A situação é calculada na tela (design, "Ajustes na implementação").
- [ ] 2.5 O aviso `prazo_vencendo` na rotina diária, idempotente (D7; depende de `notificacoes-de-publicacao`). Verificar: duas execuções seguidas avisam uma vez só.
  - **Em parte (20/11/2026):** publicado (passo 11 da rotina e o tipo `prazo_vencendo`); em simulação a rotina roda e conta 0. Falta rodar duas vezes depois de um alerta atingido (pedido de teste 11, SLA de 1 hora, vence em 23/11 às 01:00, porque 20/11 é feriado).

## 3. Testar

- [x] 3.1 HTTP, prazo:
  - **passa:** sem configuração, o pedido aberto agora recebe o prazo esperado pela regra do D2 (a conferência calcula o esperado com a tabela de feriados);
  - **falha:** o pedido LGPD nunca passa de `prazo_resposta`.
  - **Feito (20/11/2026):** o prazo e o alerta batem com a regra recalculada no teste a partir da tabela de feriados; o pedido LGPD não passa do prazo legal.
- [x] 3.2 HTTP, configuração:
  - **passa:** o Admin muda Desligamento para 24 horas, e o pedido novo usa 24 horas enquanto o antigo mantém o prazo;
  - **falha:** RH e Gestor recebem 403, e 0 ou 721 horas dão 400.
  - **Feito (20/11/2026):** Desligamento com 24 horas, o pedido novo com 1 dia útil e o antigo com o prazo anterior; RH e Gestor 403; 0, 721 e LGPD com 241 dão 400. A configuração voltou ao padrão.
- [ ] 3.3 HTTP, situação: um pedido de teste com o prazo vencido aparece "vencido" e no topo da `central_de_tarefas`; um recém-aberto aparece "no prazo".
  - **Pendente (20/11/2026):** a solicitação "Outra" não entra na `central_de_tarefas`; refazer com um pedido de desligamento de SLA de 1 hora útil num dia útil e conferir depois de 1 hora.
- [x] 3.4 `docs/regras-de-negocio.md` (seção nova, com a tabela do D1 e o cálculo do D2) depois da implementação. Verificar: `openspec validate sla-de-solicitacoes`.
  - **Feito (20/11/2026):** seção 25.
