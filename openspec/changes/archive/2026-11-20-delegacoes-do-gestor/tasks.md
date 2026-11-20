# Tasks

- [x] 1. Conferir Figma F17 e contratos de listagem/cancelamento, registrando limites autorizados.
- [x] 2. Criar modelo, consultas e página; integrar menu do Gestor e limpar sessão.
- [x] 3. Implementar cancelamento e criação bloqueada com estados honestos.
- [x] 4. Testar modelo, API simulada, AppTest, segurança e falhas parciais (30 testes passaram).
- [x] 5. Executar regressões solicitadas, sintaxe e validação OpenSpec.
- [x] 6. Rodar prévia Streamlit/Chrome com dados fictícios e comparar ao Figma.
- [x] 7. Documentar resultados e divergências sem concluir o F17 completo.
  Evidência: `docs/evidencias/frontend-delegacoes.md`, com capturas e referências lado a lado.
- [x] 8. Verificar por HTTP real os casos permitido/negado por perfil, quando houver sessão de teste.
  Feito (20/11/2026), com a conta de teste como Gestor. O Gestor concede uma delegação como titular e ela aparece como concedida; não cria em nome de outro titular (403). A delegação do RH para ele aparece como recebida e ele não a cancela (403). Ele cancela a própria (`cancelada_em` preenchido) e não cancela de novo (400). As duas delegações de teste ficaram canceladas.
- [x] 9. Dependências futuras de backend: catálogo seguro para criação, filas delegadas, demais
  escopos e alinhamento da hierarquia. Fora do escopo desta implementação; manter pendente.
  Transferida (20/11/2026) para a change `backend-gestor-pendencias`, tarefa 4.1.
