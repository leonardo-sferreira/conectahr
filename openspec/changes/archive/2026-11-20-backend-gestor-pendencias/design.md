# Design

## Context

Ver `proposal.md`. Este documento traz as decisões tomadas. As dos itens 3 a 5 (D2 a D5) foram escolhidas pelo responsável pelo projeto em 20/11/2026, entre as alternativas apresentadas.

## Decisions

### D1. Cadastro de competências de avaliação (tarefa 2.1)

- **Rotas** (grupo Colaboradores, só RH e Admin, com a guarda completa de sessão):
  - `competencias_avaliacao` GET lista todas, ativas e inativas;
  - `competencias_avaliacao` POST cria uma competência, que entra ativa;
  - `competencias_avaliacao/{id}` PATCH edita, desativa ou reativa.
- **Tabela:** `competencia_avaliacao` já existia (nome, descrição, categoria, nível, peso e ativo). Não há mudança de schema.
- **Sem exclusão:** respostas (`resposta_avaliacao`) e reconhecimentos guardam o id da competência. Desativar tira a competência do formulário e preserva o histórico.
- **Validação no backend:** nome de 3 a 200 caracteres; categoria e nível dentro dos enums; peso maior que 0 e até 100 (1 quando vazio). A categoria e o nível são conferidos com texto entre vírgulas, porque `contains` em lista não funciona neste workspace.
- **Auditoria:** criar, editar e desativar, cada uma com a sua ação.
- **Seleção no formulário:** sem mudança. Valem as ativas do nível do avaliado ou, se o nível não tiver nenhuma, todas as ativas.
- **Tela:** a seção "Competências avaliadas" fica no fim da aba "Avaliações de desempenho" de "Ciclos de avaliação" (Figma F27, etapas 4 e 5). A tabela usa o mesmo estilo da tabela de ciclos: o `theme.py` passou a aceitar `rh_tabela_comp` e cabeçalhos `rh_cab*`, porque uma página não pode repetir a `key` de contêiner.
- **Competências iniciais:** cinco competências genéricas no nível L1, cadastradas pela própria rota no teste com login. O RH ajusta as competências pela tela.

### D2. Indicadores da equipe só com agregados do setor (tarefa 3.1; decisão de 20/11/2026)

- **Rota nova `indicadores_equipe` GET** (Gestor; o setor é o departamento em que `gestor_colaborador_id` é a ficha dele). Devolve os últimos 6 meses do setor inteiro, sem nomes nem ids de pessoas:
  - `pessoas`: fichas não desligadas do setor, sem o próprio Gestor;
  - por mês: `horas_extras` (soma de `registro_ponto.horas_extras`), `ausencias` (registros Aprovada ou Registrado que cobrem o mês) e `absenteismo` (dias úteis cobertos por ausência Aprovada ou Registrado ÷ pessoas × dias úteis do mês, em %; dias úteis: segunda a sexta, sem feriados nacionais);
  - `banco_horas`: saldo atual do setor (créditos menos débitos de `banco_horas_lancamento`);
  - `clima`: % de respostas favoráveis (nota 4 ou 5 na escala de concordância) do setor na última pesquisa de clima encerrada, com a quantidade de participantes.
- **Privacidade:**
  - setor com menos de 5 pessoas devolve os números vazios, com o motivo;
  - o clima segue o mínimo de respostas da pesquisa;
  - a folha individual continua com o escopo de hoje (superior direto; sem ele, o gestor do departamento).
- **CSV:** `indicadores_equipe/exportar` POST devolve os mesmos agregados e grava a auditoria `exportar_indicadores_equipe` (setor e período, sem dados de pessoas). A tela gera o arquivo.

### D3. Delegações do Gestor (tarefa 4.1; decisão de 20/11/2026)

- **Escopos do Gestor:** só `ferias`, `correcao_ponto` e `todas`, que são as decisões dele. Os outros escopos (ausência, documento, desligamento e solicitação ao RH) são decisões do RH: o Gestor recebe 400 ao tentar criá-los. RH e Admin continuam com todos os escopos.
- **Catálogo de substitutos** (`delegacoes/substitutos` GET, Gestor): pessoas ativas com conta do próprio setor e os outros Gestores ativos, com nome, cargo e setor. `delegacoes` POST feito por Gestor só aceita substituto desse catálogo.
- **Hierarquia alinhada:** o titular da delegação vale para um pedido quando é quem decidiria normalmente, ou seja, o superior direto da pessoa e, sem ele, o gestor do departamento. É a mesma regra de `notificar_decisores` e das filas. Hoje só o gestor do departamento valia.
- **Central do substituto:** com uma delegação vigente, a `central_de_tarefas` e `correcoes_ponto` GET passam a incluir os pedidos que o titular decidiria, cada um com a indicação "por delegação de {titular}".

### D4. Prazo e autoavaliação na avaliação do Gestor (tarefa 5.1; decisão de 20/11/2026)

- **Prazo:** a data de fim do ciclo. Não há campo novo.
- **Autoavaliação:** `minhas_avaliacoes` devolve, em cada avaliação de relação `gestor`, a situação da autoavaliação da mesma pessoa no mesmo ciclo (`pendente`, `em_andamento`, `enviada` ou sem autoavaliação), sem as notas nem os comentários.

### D5. Contestação respondida pelo Gestor, com a palavra final do RH (tarefa 5.1; decisão de 20/11/2026)

- **Quem responde primeiro:** o avaliador de uma avaliação de relação `gestor` contestada responde em `contestacoes_avaliacao/{id}/responder_gestor` POST:
  - `manter`, com justificativa;
  - `revisar`, com uma nota de 1 a 5 e justificativa. A nota revisada passa a valer na avaliação, e a nota original fica guardada (`avaliacao.nota_original`).
- **Situação:** a contestação continua `aberta` até o RH responder. `contestacoes_equipe` GET lista para o Gestor as contestações das avaliações que ele fez.
- **RH:** `revisar` aceita opcionalmente uma nota final de 1 a 5, que vale sobre a do Gestor, mantendo a original guardada. Responder fecha a contestação (`revisada`).
- **Campos novos:**
  - em `contestacao_avaliacao`: `decisao_gestor`, `nota_revisada`, `resposta_gestor`, `respondido_gestor_em` e `respondido_gestor_por_user_id`;
  - em `avaliacao`: `nota_original`.
- **Auditoria:** `responder_contestacao_gestor`, com a decisão e as notas anterior e nova.

## Ajustes na implementação (20/11/2026)

- **Cálculo dos indicadores:** fica na função `ConectaHR/indicadores_setor`, usada pelas duas rotas. O mínimo de pessoas é parâmetro: as rotas sempre passam 5; a conferência pela CLI usou 1.
- **Cartão de clima:** vira "Clima (favorável)", com a % de respostas favoráveis, e não o eNPS do rótulo original do Figma.
- **"Ausências por tipo" do Figma:** vira "Ausências por mês", porque a rota agregada conta por mês.
- **Tela de contestação do RH:** passa a mostrar a resposta do Gestor. Para isso, `ciclos_avaliacao_rh` devolve `decisao_gestor`, `nota_revisada`, `resposta_gestor` e `nota_original`.

## Risks / Trade-offs

- [Competências iniciais genéricas] → servem para destravar as avaliações; o RH pode trocá-las e criar competências por nível.
- [Peso ainda não entra na nota] → a nota geral continua sendo a média simples das respostas (`avaliacoes/{id}/enviar`); usar o peso é uma decisão para a tarefa 5.1.
