# Proposal

## Why

O usuário pediu (20/10/2026) a prioridade 1 da pesquisa de mercado: funções que a lei exige.

Desde 26/05/2026, a NR-1 exige que o gerenciamento de riscos ocupacionais (GRO/PGR) inclua os riscos psicossociais. A empresa precisa:
- identificar, avaliar, controlar e monitorar esses riscos;
- manter inventário, plano de ação e evidência de que os trabalhadores participaram;
- olhar para as condições de trabalho, não para diagnósticos individuais.

O ConectaRH já tem uma pesquisa anônima por setor (a de clima), mas não tem questionário próprio, cálculo de risco, plano de ação nem relatório para o PGR.

## What Changes

- **Avaliação** (D1):
  - a pesquisa de clima ganha o tipo `psicossocial`;
  - as perguntas ganham a escala de frequência, a dimensão e o sentido (risco ou proteção);
  - questionário padrão: 16 perguntas em 8 dimensões.
- **Resultado** (D2): mapa de risco de 0 a 100 por dimensão e setor, calculado na tela a partir dos resultados agregados que já existem, com os riscos altos sem ação.
- **Plano de ação** (D3): tabela `acao_psicossocial` e endpoints para listar, criar e atualizar.
- **Relatório PGR** (D4): participação, inventário e plano, em Markdown, para baixar.
- **Telas** (D5):
  - "Riscos psicossociais" (RH);
  - a escala de frequência na "Pesquisa de clima" da pessoa;
  - o clima do RH sem as avaliações psicossociais.

## Non-goals

- Diagnóstico individual ou qualquer dado de saúde: a avaliação é sobre condições de trabalho, anônima e por setor.
- Validar cientificamente o questionário: ele é uma referência inicial; o responsável pelo PGR valida ou troca o método.
- Gerar o PGR inteiro: o relatório é o anexo psicossocial.
- Lembretes automáticos de prazo das ações: o plano não tem tarefas agendadas.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: avaliação de riscos psicossociais da NR-1, com inventário por setor, plano de ação e relatório para o PGR.

## Impact

- **Backend:**
  - tabelas alteradas: `pesquisa_clima` (`tipo`) e `pergunta_clima` (escala `frequencia`, `dimensao` e `sentido`);
  - tabela nova: `acao_psicossocial`;
  - endpoints alterados: `pesquisas_clima` POST, `pesquisas_clima/{id}/perguntas`, `minhas_pesquisas_clima` e `pesquisas_clima_rh`;
  - endpoints novos: `acoes_psicossociais` GET e POST e `acoes_psicossociais/{id}` PATCH.
- **Frontend:** `api_client.py`, `clima_modelo.py`, `psicossocial_modelo.py`, `pagina_riscos_psicossociais.py`, `pagina_pesquisa_clima.py`, `pagina_pesquisas_clima.py`, `app.py` e `theme.py`.
- **Figma:** seção 21 (545:1272).
- **Testes:** `tools/testar_riscos_psicossociais.py`.
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção 20);
  - `docs/lgpd/registro-de-operacoes.md` (F15 e cobertura);
  - `docs/figma-pendencias.md`.
- **Dependência:** parte da branch do canal de denúncias (#86).
