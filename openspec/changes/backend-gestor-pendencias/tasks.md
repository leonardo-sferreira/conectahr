# Tasks

## 1. Especificação

- [x] 1.1 Detalhar specs e design de cada item da proposta e dividir em changes menores, se for o caso. Verificar: `openspec validate backend-gestor-pendencias`.
  - **Feito (20/11/2026):** decisões D2 a D5 escolhidas pelo responsável pelo projeto; requisitos e cenários na spec. A change não foi dividida: as tarefas abaixo separam as frentes.

## 2. Competências de avaliação

- [x] 2.1 Cadastro de competências de avaliação (RH/Admin), com nível e ativo, e as competências iniciais. Verificar: uma avaliação atribuída mostra o formulário com competências; o Gestor salva rascunho e envia.
  - **Feito (20/11/2026):** `competencias_avaliacao` GET e POST e `competencias_avaliacao/{id}` PATCH publicados (dry-run só com 3 `CREATE`; `checar_endpoints` 283, 0 falhas); seção "Competências avaliadas" na aba "Avaliações de desempenho", desenhada antes no Figma (F27, etapas 4 e 5); `tools/testar_clima_avaliacao.py` 64/64. Com login, 19/19: Colaborador recebe 403 para listar, cadastrar e editar; categoria, nível e nome inválidos recebem 400; o RH cadastrou as 5 iniciais (D1) e desativou e reativou uma delas. Num ciclo de teste (4, cancelado no fim), com a conta de teste como Gestor só durante o teste: o formulário trouxe as 5, o rascunho foi salvo, quem não é o avaliador recebeu 403 ao responder e ao enviar, nota 6 recebeu 400, o Gestor enviou, e a avaliação enviada não aceitou mudança (400).

## 3. Indicadores da equipe (F18)

- [ ] 3.1 Cobertura do departamento inteiro, absenteísmo com jornada histórica, clima agregado ao Gestor e exportação CSV auditada.
  - [ ] 3.1.1 `indicadores_equipe` GET e `indicadores_equipe/exportar` POST (D2). Verificar: `checar_endpoints`; por HTTP, Gestor 200 e Colaborador 403; setor com menos de 5, números vazios.
  - [ ] 3.1.2 "Indicadores da equipe" usando a rota nova (absenteísmo, clima e CSV deixam de ser indisponíveis). Verificar: `tools/testar_indicadores_equipe.py`.

## 4. Delegações do Gestor (F17)

- [ ] 4.1 Catálogo de substitutos, filas delegadas na Central, efeito nos demais escopos e alinhamento da hierarquia.
  - [ ] 4.1.1 `delegacoes/substitutos` GET; `delegacoes` POST com os escopos e o catálogo do Gestor; titular pela regra do superior direto em férias e correção de ponto (D3). Verificar: por HTTP, escopo do RH 400, substituto fora do catálogo 400.
  - [ ] 4.1.2 `central_de_tarefas` e `correcoes_ponto` GET com os pedidos delegados (D3). Verificar: por HTTP, o substituto vê o pedido do titular durante a delegação e deixa de ver depois de cancelada.
  - [ ] 4.1.3 "Nova delegação" com o catálogo, e a Central indicando "por delegação". Verificar: `tools/testar_delegacoes.py`.

## 5. Avaliações da equipe (F15)

- [ ] 5.1 Autoavaliação confirmável, prazos e contestação respondida pelo Gestor (manter ou revisar a nota).
  - [ ] 5.1.1 `minhas_avaliacoes` com o prazo e a situação da autoavaliação (D4). Verificar: por HTTP, sem notas da autoavaliação na resposta.
  - [ ] 5.1.2 Campos de D5, `contestacoes_equipe` GET, `contestacoes_avaliacao/{id}/responder_gestor` POST e a nota final opcional no `revisar` do RH. Verificar: por HTTP, o avaliador revisa (nota nova, original guardada), outro usuário 403, o RH fecha com a nota final.
  - [ ] 5.1.3 "Avaliações da equipe" com o prazo, a autoavaliação e a aba de contestações com "Manter" e "Revisar"; a tela do RH com a nota final. Verificar: `tools/testar_avaliacoes_equipe.py` e `tools/testar_clima_avaliacao.py`.
