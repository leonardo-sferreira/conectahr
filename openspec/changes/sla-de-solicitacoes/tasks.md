# Tasks

Cada tarefa tem o critério de verificação. Os testes por HTTP rodam contra o Xano real, com um caso que passa e um que falha, por perfil. As evidências vão para `docs/evidencias/sla-de-solicitacoes.md`, sem dado pessoal.

## 1. Tela

- [ ] 1.1 Figma, antes de codar, nos temas claro e escuro. Verificar: print dos nós.
  - a aba "SLA de solicitações" em Configurações: a tabela por setor e tipo e o modal de edição (Admin), e a leitura (RH);
  - o selo "Responder até" nas filas, na Central de Pendências e em "Meus pedidos".
- [ ] 1.2 `sla_modelo.py`: a situação, o selo e a ordem (D5, D6). Verificar: regras em `tools/testar_sla.py`.
- [ ] 1.3 A aba "SLA de solicitações", com os 6 estados (carregando, vazio, sucesso, erro, bloqueado e permissão negada); o RH só lê e o Gestor não vê a aba (D4, D6). Verificar: `tools/testar_sla.py`.
- [ ] 1.4 O selo nas filas (Central de Pendências, Solicitações ao RH, Desligamentos, Férias, Ausências, Folha de ponto e Usuários e perfis) e em "Meus pedidos" (D6). Verificar: os testes de cada tela conferem o selo, e "Sem prazo" nos pedidos antigos.

## 2. Integrar

- [ ] 2.1 A tabela `sla_config` e os campos `prazo_sla`, `alerta_sla`, `sla_horas` e `aviso_sla_em` nas 6 tabelas de pedido (D1, D3). Verificar: dry-run só com `CREATE` e `ADD_FIELD`.
- [ ] 2.2 `ConectaHR/somar_horas_uteis` e `ConectaHR/prazo_sla` (D2, D3). Verificar: os quatro exemplos do D2 (segunda, sexta, sábado e semana com feriado) num endpoint de teste ou na 3.1.
- [ ] 2.3 `sla_config` GET, POST e `{id}` PATCH, só Admin para gravar, com auditoria (D4). Verificar: `checar_endpoints` e a 3.2.
- [ ] 2.4 O POST de cada tipo grava o prazo, com o teto legal no pedido LGPD; as listagens e a `central_de_tarefas` devolvem prazo e situação, em ordem (D3, D5). Verificar: a 3.1 e a 3.3.
- [ ] 2.5 O aviso `prazo_vencendo` na rotina diária, idempotente (D7; depende de `notificacoes-de-publicacao`). Verificar: duas execuções seguidas avisam uma vez só.

## 3. Testar

- [ ] 3.1 HTTP, prazo:
  - **passa:** sem configuração, o pedido aberto agora recebe o prazo esperado pela regra do D2 (a conferência calcula o esperado com a tabela de feriados);
  - **falha:** o pedido LGPD nunca passa de `prazo_resposta`.
- [ ] 3.2 HTTP, configuração:
  - **passa:** o Admin muda Desligamento para 24 horas, e o pedido novo usa 24 horas enquanto o antigo mantém o prazo;
  - **falha:** RH e Gestor recebem 403, e 0 ou 721 horas dão 400.
- [ ] 3.3 HTTP, situação: um pedido de teste com o prazo vencido aparece "vencido" e no topo da `central_de_tarefas`; um recém-aberto aparece "no prazo".
- [ ] 3.4 `docs/regras-de-negocio.md` (seção nova, com a tabela do D1 e o cálculo do D2) depois da implementação. Verificar: `openspec validate sla-de-solicitacoes`.
