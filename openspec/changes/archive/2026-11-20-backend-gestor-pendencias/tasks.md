# Tasks

## 1. Especificação

- [x] 1.1 Detalhar specs e design de cada item da proposta e dividir em changes menores, se for o caso. Verificar: `openspec validate backend-gestor-pendencias`.
  - **Feito (20/11/2026):** decisões D2 a D5 escolhidas pelo responsável pelo projeto; requisitos e cenários na spec. A change não foi dividida: as tarefas abaixo separam as frentes.

## 2. Competências de avaliação

- [x] 2.1 Cadastro de competências de avaliação (RH/Admin), com nível e ativo, e as competências iniciais. Verificar: uma avaliação atribuída mostra o formulário com competências; o Gestor salva rascunho e envia.
  - **Feito (20/11/2026):** `competencias_avaliacao` GET e POST e `competencias_avaliacao/{id}` PATCH publicados (dry-run só com 3 `CREATE`; `checar_endpoints` 283, 0 falhas); seção "Competências avaliadas" na aba "Avaliações de desempenho", desenhada antes no Figma (F27, etapas 4 e 5); `tools/testar_clima_avaliacao.py` 64/64. Com login, 19/19: Colaborador recebe 403 para listar, cadastrar e editar; categoria, nível e nome inválidos recebem 400; o RH cadastrou as 5 iniciais (D1) e desativou e reativou uma delas. Num ciclo de teste (4, cancelado no fim), com a conta de teste como Gestor só durante o teste: o formulário trouxe as 5, o rascunho foi salvo, quem não é o avaliador recebeu 403 ao responder e ao enviar, nota 6 recebeu 400, o Gestor enviou, e a avaliação enviada não aceitou mudança (400).

## 3. Indicadores da equipe (F18)

- [x] 3.1 Cobertura do departamento inteiro, absenteísmo com jornada histórica, clima agregado ao Gestor e exportação CSV auditada.
  - [x] 3.1.1 `indicadores_equipe` GET e `indicadores_equipe/exportar` POST (D2). Verificar: `checar_endpoints`; por HTTP, Gestor 200 e Colaborador 403; setor com menos de 5, números vazios.
    - **Feito (20/11/2026):** `ConectaHR/indicadores_setor` e as duas rotas publicadas; `checar_endpoints` 291, 0 falhas. Com login: o Gestor recebe o setor oculto (2 pessoas, abaixo de 5), sem dado de pessoa; RH e Admin 403; a exportação aparece na auditoria. Os dias úteis dos 6 meses conferidos pela CLI (feriados nacionais e ponto facultativo); a base não tem horas extras nem ausências no período, então as somas só foram conferidas com zero.
  - [x] 3.1.2 "Indicadores da equipe" usando a rota nova (absenteísmo, clima e CSV deixam de ser indisponíveis). Verificar: `tools/testar_indicadores_equipe.py`.
    - **Feito (20/11/2026):** a tela usa só a rota agregada; `tools/testar_indicadores_equipe.py` 34/34 (tela reescrita; o modelo antigo continua testado).

## 4. Delegações do Gestor (F17)

- [x] 4.1 Catálogo de substitutos, filas delegadas na Central, efeito nos demais escopos e alinhamento da hierarquia.
  - [x] 4.1.1 `delegacoes/substitutos` GET; `delegacoes` POST com os escopos e o catálogo do Gestor; titular pela regra do superior direto em férias e correção de ponto (D3). Verificar: por HTTP, escopo do RH 400, substituto fora do catálogo 400.
    - **Feito (20/11/2026):** publicados. Com login: escopos do Gestor férias, correção de ponto e todas; catálogo com o setor, sem o titular e só com nome e setor; desligamento e solicitação ao RH 400; substituto fora do catálogo 400; delegação válida criada e cancelada. A regra do titular (superior direto; sem ele, gestor do departamento) vale em aprovar e rejeitar férias e correção de ponto.
  - [x] 4.1.2 `central_de_tarefas` e `correcoes_ponto` GET com os pedidos delegados (D3). Verificar: por HTTP, o substituto vê o pedido do titular durante a delegação e deixa de ver depois de cancelada.
    - **Feito, com ressalva (20/11/2026):** publicados. Não conferido por HTTP: a base só tem 2 pessoas no setor que tem gestor, e o caso precisa de uma terceira pessoa, sem ser o titular nem o substituto, com pedido pendente. A regra é a mesma das filas do próprio Gestor.
  - [x] 4.1.3 "Nova delegação" com o catálogo, e a Central indicando "por delegação". Verificar: `tools/testar_delegacoes.py`.
    - **Feito (20/11/2026):** `tools/testar_delegacoes.py` 31/31 (criação com o catálogo, validação e recusa do backend) e `tools/testar_decisoes.py` 64/64.

## 5. Avaliações da equipe (F15)

- [x] 5.1 Autoavaliação confirmável, prazos e contestação respondida pelo Gestor (manter ou revisar a nota).
  - [x] 5.1.1 `minhas_avaliacoes` com o prazo e a situação da autoavaliação (D4). Verificar: por HTTP, sem notas da autoavaliação na resposta.
    - **Feito (20/11/2026):** com login, prazo = fim do ciclo; autoavaliação pendente e depois enviada, sem notas nem comentários.
  - [x] 5.1.2 Campos de D5, `contestacoes_equipe` GET, `contestacoes_avaliacao/{id}/responder_gestor` POST e a nota final opcional no `revisar` do RH. Verificar: por HTTP, o avaliador revisa (nota nova, original guardada), outro usuário 403, o RH fecha com a nota final.
    - **Feito (20/11/2026):** com login, o Gestor vê a contestação; outra conta 403; revisar sem nota 400; nota 2 revisada para 3 com a original guardada; responder de novo 400; continua aberta; o Admin fecha com nota final 4 e a original continua 2.
  - [x] 5.1.3 "Avaliações da equipe" com o prazo, a autoavaliação e a aba de contestações com "Manter" e "Revisar"; a tela do RH com a nota final. Verificar: `tools/testar_avaliacoes_equipe.py` e `tools/testar_clima_avaliacao.py`.
    - **Feito (20/11/2026):** `tools/testar_avaliacoes_equipe.py` 32/32 e `tools/testar_clima_avaliacao.py` 66/66.
