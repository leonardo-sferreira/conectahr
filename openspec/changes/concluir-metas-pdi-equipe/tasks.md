## Implementação parcial autorizada
- [x] Preservar ciclo anual e modal compartilhado com RH/Admin.
- [x] Compor F16 com abas, filtro indisponível, tabela e cartões, sem consumir fontes inseguras.
- [x] Isolar cache anual por token/usuário e limpar estados ao sair/trocar conta.
- [x] Criar suíte de segurança, sessão, estados, navegação e temas; integrar à validação local/CI.
- [x] Executar suíte nova (20 testes) e regressões relevantes (41 verificadores/suítes do workflow, incluindo a nova).
- [x] Validar sintaxe, OpenSpec strict e git diff --check.
- [x] Executar Streamlit e registrar evidências clara/escura comparadas ao Figma em docs/evidencias/frontend-metas-pdi-equipe.md.

## Fora desta implementação — não concluído
- [x] Contratos seguros para metas/PDI da equipe e criação departamental. (Feito nas tarefas 6 e 7, em 22/11/2026.)
- [x] Check-in autorizado para liderança, se aprovado como regra futura. (Aprovado em D3; feito na tarefa 8.)
- [x] Contrato e desenho compatíveis para agendamento de reuniões 1:1. (D4; feito nas tarefas 9 e 10.)
- [x] Verificação HTTP real e notificações transacionais com contas autorizadas, sem modificar Xano nesta tarefa. (Feita em 22/11/2026; ver a tarefa 12.)
- [x] Concluir integralmente o F16 após resolver as dependências. (Tarefa 11.)

## Depois das decisões de 22/11/2026 (design.md, D1 a D5)

- [x] 6 Backend:
  - `minha_equipe/metas_pdi` GET: só os liderados diretos, com título, prazo, progresso e situação das metas e do PDI (D1).
  - Verificar com `checar_endpoints` e por HTTP:
    - o gestor vê só os liderados diretos;
    - quem não é gestor deles recebe 403.
- [x] 7 Backend: autorização de `metas` POST e de `pdi` POST para o gestor, só no próprio departamento e nos liderados diretos (D2). Verificar por HTTP: passa no liderado direto e dá 403 em quem é de fora.
- [x] 8 Backend: `metas/{id}/checkin` POST aceita o gestor direto, gravado em nome dele e auditado (D3). Verificar por HTTP: passa como gestor direto e dá 403 para outro gestor.
- [x] 9 Backend: reuniões 1:1 (D4).
  - `reuniao_individual` ganha hora, pauta e situação;
  - endpoints para agendar, marcar como realizada, cancelar e listar, só entre o gestor e os liderados diretos;
  - avisos no sino e por e-mail ao agendar e ao cancelar (D5).
  - Verificar por HTTP com um gestor e um liderado.
- [x] 10 Figma: conferir o F16 (seção 248:1405) com as decisões, nos temas claro e escuro, e ajustar o que faltar (agendar, cancelar, check-in do líder).
- [x] 11 Frontend: completar o F16 em "Metas da equipe", com abas, filtro de pessoa, Nova meta, Check-in, PDI e reuniões 1:1, e os seis estados. Verificar com o `tools/testar_metas_equipe.py` estendido e com o Chrome em 390 px.
- [x] 12 Evidência, `docs/regras-de-negocio.md` e testes HTTP: passa e falha por perfil, com o login de um gestor e de um liderado dele.

### Notas (22/11/2026)

A evidência está em `docs/evidencias/frontend-metas-pdi-equipe.md`, na seção de atualização.

- **6 a 9:** backend publicado no Xano. As expressões rodaram numa função temporária, e `checar_endpoints` passa com 308 endpoints. A parte "por HTTP" de cada tarefa fica para a 12.
- **10:** caminhos novos no Figma: "Reunião 1:1" (`644:886`; escuro `644:2840`) e "Nova ação de PDI" (`644:1522`; escuro `644:3455`). No escuro, nenhum texto ficou abaixo de 3:1.
- **11:** `tools/testar_metas_equipe.py` passa 32 de 32, e `tools/testar_trajetoria.py`, 49 de 49. A revisão independente não achou nada grave, e o que ela apontou foi corrigido (detalhes na evidência). Também conferido no Chrome em 1440 e em 390 px.
- **12:** `docs/regras-de-negocio.md` ganhou a seção 11.3a e a tabela 11.4 foi atualizada. HTTP feito em 22/11/2026: 39 de 39 verificações, que incluem as tarefas 33 e 57 da `concluir-frontend-streamlit`. A conta Colaborador virou Gestor só durante o teste, com a ficha do RH como liderada direta, e tudo voltou ao que era.
