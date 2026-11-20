# Design

## Context

Ver proposal.md. A pesquisa de clima já garante o anonimato:
- contador agregado por pergunta, setor e nota, sem resposta individual;
- participação separada, só para impedir responder duas vezes;
- resultados só depois do encerramento e só para grupos com o mínimo de respostas, com supressão complementar.

Reaproveitar essa estrutura evita um segundo sistema de anonimato e um segundo questionário para as pessoas responderem.

## Decisions

### D1. Avaliação como pesquisa de tipo psicossocial

- `pesquisa_clima.tipo`: `clima` (o padrão) ou `psicossocial`.
- `pergunta_clima`:
  - escala `frequencia`, de 1 a 5 (nunca, raramente, às vezes, frequentemente, sempre), aceita no envio como as outras de 1 a 5;
  - `dimensao` (texto);
  - `sentido`: `risco` (quanto mais frequente, pior) ou `protecao`.
- `pesquisas_clima` POST aceita `tipo` e, em cada pergunta, a dimensão e o sentido. O resto (respostas, encerrar, resultados, adesão) não muda.
- O questionário padrão fica no frontend (`psicossocial_modelo.QUESTIONARIO`): 16 perguntas, 2 por dimensão, sobre condições de trabalho. É uma referência inicial, inspirada nos fatores de risco psicossocial da gestão de riscos ocupacionais. O responsável pelo PGR valida o método.

### D2. Resultado calculado na tela

- `pesquisas_clima/{id}/resultados` já devolve a média por pergunta e setor (e no geral), com os grupos abaixo do mínimo suprimidos.
- O risco de cada pergunta vai de 0 a 100: `risco` = (média − 1) / 4; `protecao` = (5 − média) / 4.
- O risco da dimensão é a média das perguntas dela.
- Níveis: até 33 baixo, de 34 a 66 moderado, a partir de 67 alto.
- Setor sem resultado aparece como "—".
- Sem endpoint novo: o cálculo é simples e o backend não precisa conhecer o método.

### D3. Plano de ação

- `acao_psicossocial` guarda:
  - a avaliação e o setor (0 = empresa);
  - a dimensão e o nível do risco;
  - a medida, o responsável e o prazo;
  - a situação (`planejada`, `em_andamento`, `concluida`, `cancelada`) e a data de conclusão.
- `acoes_psicossociais` GET (filtro opcional pela avaliação), POST (só em avaliação psicossocial) e `{id}` PATCH (situação e, se vierem, medida, responsável e prazo). Só RH e Admin; as escritas são auditadas.
- Na tela, a ação aberta com prazo vencido aparece como "Atrasada".

### D4. Relatório PGR

Markdown gerado na tela com:
- a avaliação e o período;
- a participação (adesão geral e por setor, como evidência de participação);
- o inventário (mapa de risco);
- o plano de ação da avaliação;
- uma nota sobre o método.

O relatório fica disponível para baixar.

### D5. Telas (Figma, seção 21, 545:1272)

- **"Riscos psicossociais"** (menu RH), com as abas:
  - **Avaliações:** cartões com adesão por setor, "Encerrar avaliação" e "Nova avaliação" (548:1916), com o questionário visível e uma pergunta extra;
  - **Resultado** (545:1274): o mapa e "Riscos altos sem ação" com "Criar ação", que abre o modal 548:1592 já preenchido;
  - **Plano de ação** (548:1287): indicadores, tabela e "Atualizar";
  - **Relatório PGR**.
- **"Pesquisa de clima"** (a pessoa): a escala de frequência mostra os nomes (548:1951).
- **"Pesquisas de clima"** (RH): não lista as avaliações psicossociais.

## Risks / Trade-offs

- [Método sem validação científica] → aviso na tela e no relatório; o questionário fica num lugar só do código, fácil de trocar.
- [Setores pequenos sem resultado] → a supressão é necessária para o anonimato; o resultado da empresa continua aparecendo.
- [Ações sem lembrete] → o indicador "Atrasadas" na tela.

## Migration Plan

1. Tabelas: `ADD_FIELD` de `tipo`, `dimensao` e `sentido`; `UPDATE_FIELD` da escala; `CREATE` de `acao_psicossocial`.
2. Endpoints: `UPDATE` e `CREATE`, conferidos contra o que está no ar.

Rollback: publicar as versões do git. As colunas novas podem ficar.
