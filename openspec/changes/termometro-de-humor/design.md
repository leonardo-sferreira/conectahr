# Design

## Context

Ver proposal.md. O termômetro segue o desenho de anonimato da pesquisa de clima: a nota só soma num contador, e a participação fica numa tabela à parte, sem a nota. Humor pode revelar algo sobre saúde. Por isso nada individual é guardado, e o resultado só aparece em grupos com o mínimo de pessoas.

## Decisions

### D1. Ciclos de 10 dias

- **Ciclo 0:** de 21/10/2026 a 30/10/2026; o ciclo n começa 10 × n dias depois.
- **Cálculo no backend:**
  - `ciclo = floor((dia juliano de hoje − 2461335) / 10)`, com hoje no fuso de São Paulo;
  - o dia juliano sai do ano, do mês e do dia, só com contas inteiras, porque não há subtração de datas no XanoScript usado no projeto;
  - 2461335 é o dia juliano de 21/10/2026.
- **A tela** calcula as datas de início e fim a partir do número do ciclo, só para mostrar.

### D2. Dados

- **`humor_contagem`:** ciclo, departamento (0 = sem departamento), nota (1 a 5) e quantidade. A chave é única por (ciclo, departamento, nota), sem `created_at`.
- **`humor_motivo_contagem`:** ciclo, departamento, motivo e quantidade, também sem data.
  - O motivo é contado à parte da nota, para não ligar uma coisa à outra.
  - Lista fechada: carga de trabalho, reconhecimento, liderança, colegas, comunicação, estrutura e ferramentas.
- **`humor_participacao`:** ciclo e pessoa, com a chave única. Não tem nota, motivo nem data; serve só para bloquear a segunda resposta.

### D3. Responder

- **`humor` GET** (qualquer perfil com ficha): devolve o ciclo de hoje e se a pessoa já respondeu.
- **`humor` POST** com nota e motivo opcional. Recusa:
  - pessoa desligada;
  - nota fora de 1 a 5;
  - motivo fora da lista;
  - quem já respondeu o ciclo.
- **Ao gravar:** soma 1 no contador do (ciclo, setor da pessoa, nota) e, com motivo, no do motivo; depois grava a participação.
- **Não é auditado individualmente**, porque a auditoria guardaria quem respondeu e quando, perto da nota. O registro da participação já basta.

### D4. Resultados

`humor/resultados` GET, com `departamento_id` opcional.

- **Quem vê:**
  - **RH e Admin:** todos os setores; o filtro limita a um.
  - **Gestor:** os setores em que é `gestor_colaborador_id`; outro setor é recusado; sem setor, 403.
- **Últimos 9 ciclos (90 dias):** em cada ciclo, a quantidade de respostas e a distribuição das 5 notas no escopo. A distribuição só sai com o mínimo de respostas.
- **Por departamento**, no ciclo atual e no anterior: a quantidade e a distribuição. Abaixo do mínimo, só "suprimido".
  - **Supressão por subtração:** se, num ciclo, só um setor ficar abaixo do mínimo, o menor dos outros também é suprimido. Assim o total menos os setores visíveis não revela o setor pequeno.
- **Motivos do ciclo atual:** só com o mínimo de respostas no escopo.
- **Participação:** quem respondeu no ciclo atual e o total de pessoas ativas no escopo.
- **Mínimo:** a variável de ambiente `INDICADORES_MINIMO_PESSOAS` (padrão 5), a mesma dos indicadores.

### D5. Telas

- **Início (Figma 563:853):**
  - o cartão "Como você está se sentindo no trabalho?", com 5 opções, o motivo opcional, "Agora não" (some até a próxima sessão) e "Enviar";
  - depois de responder, "Obrigado!" com a data do próximo ciclo (563:971), só nesta sessão;
  - respondido o ciclo, o Início não chama mais a rota até a sessão acabar.
- **"Termômetro de humor" (Figma 564:855):** no grupo RH (RH e Admin) e no grupo Equipe (Gestor). Mostra:
  - os indicadores (humor médio, bem ou muito bem, mal ou muito mal, participação);
  - a evolução em 9 ciclos;
  - os departamentos com a variação sobre o ciclo anterior (−0,3 ou menos = "Atenção");
  - o que mais pesou.
  - As médias são calculadas na tela, a partir da distribuição.

## Risks

- **Setor pequeno:** a supressão abaixo de 5 e por subtração evita a identificação. Um setor com menos de 5 pessoas nunca aparece sozinho, só no total.
- **Quem responde na hora:** quem tem acesso direto ao banco poderia ver o contador subir logo depois de uma participação. É a mesma limitação do clima, já registrada no RIPD.
- **Cansaço:** a cada 10 dias, e o "Agora não" respeita a pessoa. A resposta é voluntária.
