# Design

## Context

Ver proposal.md.

A pesquisa de clima é anônima desde a change `corrigir-brechas-e-alinhar-documentacao`:
- a nota só soma num contador por pergunta, departamento e nota (`resposta_clima_agregado`, sem data);
- `resposta_clima_participacao` só impede responder duas vezes;
- os resultados só abrem depois do encerramento e só para grupos com o mínimo de respostas da pesquisa, com supressão complementar quando um único grupo fica de fora.

O ciclo de avaliação de desempenho (`ciclo_avaliacao`) vai de planejamento a em andamento, fechamento e concluído, ou é cancelado. As avaliações (`avaliacao`) são preenchidas por competência na Trajetória e podem ser contestadas.

A tela "Ciclos de avaliação" do RH já existe para o ciclo anual de metas (change `ciclo-de-metas`). Ela ganha duas abas, em vez de uma tela nova, porque o menu do RH tem um único item "Ciclos de avaliação".

## Decisions

### D1. Escala e comentário

- `pergunta_clima.escala` tem dois valores:
  - `concordancia`: 1 a 5. É o padrão, como nas perguntas que já existem.
  - `nps`: 0 a 10.
- `resposta_clima_agregado.nota` passa a aceitar de 0 a 10. A faixa válida é conferida pela escala da pergunta.
- `comentario_clima` tem só `pesquisa_clima_id` e `texto`: sem colaborador, departamento, `created_at` ou qualquer data. O RH lê os comentários:
  - em ordem alfabética e sem o id, porque a ordem de gravação poderia ser cruzada com a das participações;
  - só depois do encerramento;
  - só quando o número de pessoas que responderam atinge o mínimo da pesquisa.

### D2. Responder de uma vez

- `minhas_pesquisas_clima` GET, para qualquer perfil com ficha: as pesquisas que já começaram, das mais novas para as mais antigas, com:
  - `aberta`: ativa e no prazo;
  - `respondida`: todas as perguntas respondidas;
  - nas abertas, as perguntas que faltam.
- `pesquisas_clima/{id}/responder` POST recebe `respostas` (lista de `{pergunta_id, nota}`) e o `comentario` opcional:
  - confere tudo antes de gravar: cada pergunta que falta precisa de nota na escala. A nota é lida como texto porque `!= null` trata 0 como nulo nesta plataforma;
  - grava numa transação;
  - para quem já respondeu tudo: "Você já respondeu esta pesquisa".
- O endpoint por pergunta continua, com a faixa pela escala, mas a tela não o usa.

### D3. RH da pesquisa

- `pesquisas_clima_rh` GET devolve todas as pesquisas, sem mostrar quem respondeu. Cada uma traz:
  - a situação: `agendada` (antes do início), `aberta` ou `encerrada` (desligada ou vencida);
  - as perguntas;
  - `participantes`: as participações na primeira pergunta, porque o envio é de tudo de uma vez.

  A resposta traz também `elegiveis`: as fichas que não estão desligadas.
- `pesquisas_clima` POST aceita `perguntas` (lista de `{texto, escala}`, até 30) e grava tudo. A criação é auditada.
- `pesquisas_clima/{id}/perguntas` só funciona antes de a pesquisa abrir. Depois, quem já respondeu ficaria com a pesquisa incompleta.
- A tela cria com o padrão de 5 respostas por grupo. O backend aceita 2 ou mais.

### D4. Resultados

Cada linha, por departamento e geral, traz:
- a `escala`;
- a média;
- `favoraveis`: 4 e 5; no NPS, 9 e 10;
- `desfavoraveis`: 1 e 2; no NPS, 0 a 6.

A tela mostra a média, o % favorável e, na escala de recomendação, o NPS (% de promotores menos % de detratores).

A resposta traz também os nomes dos departamentos, `participantes` e os comentários (D1).

### D5. Visão do RH dos ciclos de avaliação

- `ciclos_avaliacao_rh` GET, numa chamada:
  - os ciclos ativos, com as contagens (`total`, `enviadas`, `abertas`, `canceladas`);
  - as contestações abertas, com os nomes (avaliado, avaliador, ciclo), a relação e a nota;
  - os departamentos ativos;
  - as pessoas (fichas não desligadas).
- `ciclos_avaliacao/{id}/avaliacoes` GET: as avaliações do ciclo, com o avaliado (nome e departamento), o avaliador, a relação, a situação, a nota e a data de envio.

### D6. Atribuição em lote

`ciclos_avaliacao/{id}/atribuir` POST recebe `departamento_id` (0 ou vazio = todos), `autoavaliacao` e `gestor`.

- Só funciona com o ciclo em andamento.
- Para cada ficha não desligada com conta, cria a autoavaliação, a avaliação do gestor ou as duas.
- O gestor é o superior direto; sem ele, o gestor do departamento (a mesma regra do feedback das metas). Ninguém avalia a si mesmo como gestor: esses casos contam em `sem_gestor`.
- O que já existe no ciclo (mesma pessoa, mesmo avaliador, mesma relação, não cancelada) é pulado.
- Cada avaliador recebe um aviso no sino, um por lote, conforme a preferência "Avaliações e metas".
- A atribuição é auditada.

Par, subordinado e RH continuam sendo atribuídos um a um, por `avaliacoes` POST.

### D7. Concluir ou cancelar o ciclo

Ao mudar para `concluido` ou `cancelado`, as avaliações ainda pendentes ou em andamento ficam `cancelada`. A resposta diz quantas.

### D8. Telas

- **"Pesquisa de clima"** (225:4668), no menu principal de todos os perfis (o menu do Figma não tem o item):
  - o aviso de anonimato, com o mínimo da pesquisa;
  - uma pergunta por vez, com "Pergunta N de M" e a barra de progresso;
  - a escala em caixas; as notas ficam guardadas ao voltar;
  - o comentário na última pergunta e "Enviar respostas";
  - à direita, o cartão "Pesquisas", com "Em andamento", "Respondida" ou "Encerrada".
- **"Pesquisas de clima"** (RH; Figma 249:4645 e o modal 249:4885):
  - abas "Em andamento" (agendadas e abertas) e "Encerradas", e "Nova pesquisa";
  - um cartão por pesquisa: "Aberta até ... · N perguntas", a adesão geral e a de cada departamento em barras (quem respondeu, nunca o quê). Para isso, `pesquisas_clima_rh` traz `adesao_departamentos`;
  - ações "Editar perguntas" (antes de abrir; depois, "Ver perguntas"), "Encerrar pesquisa" e, nas encerradas, "Ver resultados";
  - o cartão "Resultado" da última encerrada: eNPS geral, a primeira pergunta de 1 a 5 com a média e o pior tema (a menor média);
  - o modal: nome, abre em, fecha em, as perguntas de 1 a 5 (sugeridas, uma por linha), a de 0 a 10 (opcional) e o aviso de anonimato. O mínimo é o padrão, 5 por grupo.
- **"Ciclos de avaliação"** (Figma F27: 249:5068 e o modal 249:5364):
  - a aba "Ciclos" vira "Ciclos de metas", e o subtítulo da tela passa a ser o do Figma ("Abra o ciclo, acompanhe cada etapa e feche quando terminar");
  - nova aba "Avaliações de desempenho":
    - "Ano" e "Abrir novo ciclo". O modal (nome, início, fim, autoavaliação, avaliação do gestor) cria o ciclo, já o abre e atribui a todos os ativos: três chamadas. Para isso, `ciclos_avaliacao_rh` traz, em cada ciclo, as autoavaliações e as do gestor (atribuídas e enviadas), e o lote também manda e-mail (como `avaliacoes` POST, pela preferência);
    - a tabela: ciclo (nome e descrição), período, % de autoavaliações e de avaliações do gestor enviadas (em barras) e situação ("Aberto", "Em fechamento", "Fechado"). Ações que o Figma não desenha: "Atribuir" (em lote ou uma a uma), "Ver avaliações" e as mudanças de situação, com confirmação;
    - embaixo, do ciclo em foco (o aberto, ou o de "Ver avaliações"): "Contestações do ciclo" ("avaliado → avaliador", "Aberta em", "Responder") e "Andamento por departamento" (% enviado, calculado na tela a partir de `ciclos_avaliacao/{id}/avaliacoes`).
  - O modal do Figma também tem "Avaliação de pares" e "Permitir contestação". Ficam de fora: pares não têm regra de escolha (entram uma a uma, em "Atribuir"), e a contestação já é sempre permitida.

## Risks / Trade-offs

- [Comentário que identifica a pessoa] → a tela pede para não escrever nomes. O texto não tem autor nem data e só aparece com o mínimo de respostas.
- [Respostas de antes desta change, gravadas uma a uma, deixando a pesquisa incompleta] → o envio cobre só as perguntas que faltam.
- [Lote grande e o limite do plano] → é uma chamada só; o trabalho fica no servidor.
- [Erro de execução do XanoScript] → `tools/testar_clima_avaliacao_http.py`, com login de verdade.

## Migration Plan

1. Tabelas:
   - `CREATE` de `comentario_clima`;
   - `ADD_FIELD` de `escala`, com o padrão `concordancia`;
   - `UPDATE_FIELD` da faixa da nota.
2. Endpoints: `CREATE` e `UPDATE`, conferidos contra o que está no ar.

Rollback: publicar as versões do git. A coluna `escala` pode ficar.
