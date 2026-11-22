## Implementação parcial autorizada
- [x] Preservar ciclo anual e modal compartilhado com RH/Admin.
- [x] Compor F16 com abas, filtro indisponível, tabela e cartões, sem consumir fontes inseguras.
- [x] Isolar cache anual por token/usuário e limpar estados ao sair/trocar conta.
- [x] Criar suíte de segurança, sessão, estados, navegação e temas; integrar à validação local/CI.
- [x] Executar suíte nova (20 testes) e regressões relevantes (41 verificadores/suítes do workflow, incluindo a nova).
- [x] Validar sintaxe, OpenSpec strict e git diff --check.
- [x] Executar Streamlit e registrar evidências clara/escura comparadas ao Figma em docs/evidencias/frontend-metas-pdi-equipe.md.

## Fora desta implementação — não concluído
- [ ] Contratos seguros para metas/PDI da equipe e criação departamental.
- [ ] Check-in autorizado para liderança, se aprovado como regra futura.
- [ ] Contrato e desenho compatíveis para agendamento de reuniões 1:1.
- [ ] Verificação HTTP real e notificações transacionais com contas autorizadas, sem modificar Xano nesta tarefa.
- [ ] Concluir integralmente o F16 após resolver as dependências.

## Depois das decisões de 22/11/2026 (design.md, D1 a D5)

- [ ] 6 Backend:
  - `minha_equipe/metas_pdi` GET: só os liderados diretos, com título, prazo, progresso e situação das metas e do PDI (D1).
  - Verificar com `checar_endpoints` e por HTTP:
    - o gestor vê só os liderados diretos;
    - quem não é gestor deles recebe 403.
- [ ] 7 Backend: autorização de `metas` POST e de `pdi` POST para o gestor, só no próprio departamento e nos liderados diretos (D2). Verificar por HTTP: passa no liderado direto e dá 403 em quem é de fora.
- [ ] 8 Backend: `metas/{id}/checkin` POST aceita o gestor direto, gravado em nome dele e auditado (D3). Verificar por HTTP: passa como gestor direto e dá 403 para outro gestor.
- [ ] 9 Backend: reuniões 1:1 (D4).
  - `reuniao_individual` ganha hora, pauta e situação;
  - endpoints para agendar, marcar como realizada, cancelar e listar, só entre o gestor e os liderados diretos;
  - avisos no sino e por e-mail ao agendar e ao cancelar (D5).
  - Verificar por HTTP com um gestor e um liderado.
- [ ] 10 Figma: conferir o F16 (seção 248:1405) com as decisões, nos temas claro e escuro, e ajustar o que faltar (agendar, cancelar, check-in do líder).
- [ ] 11 Frontend: completar o F16 em "Metas da equipe", com abas, filtro de pessoa, Nova meta, Check-in, PDI e reuniões 1:1, e os seis estados. Verificar com o `tools/testar_metas_equipe.py` estendido e com o Chrome em 390 px.
- [ ] 12 Evidência, `docs/regras-de-negocio.md` e testes HTTP: passa e falha por perfil, com o login de um gestor e de um liderado dele.
