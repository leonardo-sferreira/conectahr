# Tasks

- [x] 1. Conferir Figma e documentar contratos, populações e limites do escopo parcial.
- [x] 2. Criar modelo, dados e página; registrar navegação e limpeza de sessão.
- [x] 3. Implementar cobertura, falhas isoladas e indisponibilidade das métricas bloqueadas.
- [x] 4. Criar e executar testes de modelo, dados e AppTest do app real (37 passaram).
- [x] 5. Executar regressões solicitadas, sintaxe e validação OpenSpec.
- [x] 6. Rodar Streamlit com API fictícia, testar Chrome claro/escuro e comparar ao Figma.
- [x] 7. Registrar evidências e divergências, sem concluir F18 completo.
  Evidência: `docs/evidencias/frontend-indicadores-equipe.md`, com referências e capturas.
- [x] 8. Verificar por HTTP real permitido/negado por perfil quando houver sessão de teste.
  Feito (20/11/2026), com uma conta de teste promovida a Gestor do setor Recursos Humanos só durante o teste (perfil e gestor do setor devolvidos depois). Colaborador: `folha_ponto/pessoas` só com ele mesmo; banco de horas e folha de outra pessoa, 403. Gestor: `folha_ponto/pessoas` só do próprio setor, folha do mês e organograma respondem, banco de horas de quem é da equipe 200, banco de horas e folha de outro setor 403.
- [x] 9. Dependências fora desta entrega: cobertura departamental, absenteísmo histórico,
  clima autorizado e exportação auditada do Gestor. Manter pendente.
  Transferida (20/11/2026) para a change `backend-gestor-pendencias`, tarefa 3.1.

