# Tasks

## 1. Especificação

- [ ] 1.1 Detalhar specs e design de cada item da proposta e dividir em changes menores, se for o caso. Verificar: `openspec validate backend-gestor-pendencias`.

## 2. Competências de avaliação

- [x] 2.1 Cadastro de competências de avaliação (RH/Admin), com nível e ativo, e as competências iniciais. Verificar: uma avaliação atribuída mostra o formulário com competências; o Gestor salva rascunho e envia.
  - **Feito (20/11/2026):** `competencias_avaliacao` GET e POST e `competencias_avaliacao/{id}` PATCH publicados (dry-run só com 3 `CREATE`; `checar_endpoints` 283, 0 falhas); seção "Competências avaliadas" na aba "Avaliações de desempenho", desenhada antes no Figma (F27, etapas 4 e 5); `tools/testar_clima_avaliacao.py` 64/64. Com login, 19/19: Colaborador recebe 403 para listar, cadastrar e editar; categoria, nível e nome inválidos recebem 400; o RH cadastrou as 5 iniciais (D1) e desativou e reativou uma delas. Num ciclo de teste (4, cancelado no fim), com a conta de teste como Gestor só durante o teste: o formulário trouxe as 5, o rascunho foi salvo, quem não é o avaliador recebeu 403 ao responder e ao enviar, nota 6 recebeu 400, o Gestor enviou, e a avaliação enviada não aceitou mudança (400).

## 3. Indicadores da equipe (F18)

- [ ] 3.1 Cobertura do departamento inteiro, absenteísmo com jornada histórica, clima agregado ao Gestor e exportação CSV auditada.

## 4. Delegações do Gestor (F17)

- [ ] 4.1 Catálogo de substitutos, filas delegadas na Central, efeito nos demais escopos e alinhamento da hierarquia.

## 5. Avaliações da equipe (F15)

- [ ] 5.1 Autoavaliação confirmável, prazos e contestação respondida pelo Gestor (manter ou revisar a nota).
