# Proposal

## Why

O usuário pediu (20/10/2026) a pesquisa de clima e o ciclo de avaliação.

A pesquisa de clima (tarefa 48 de `concluir-frontend-streamlit`; Figma 225:4668) tem backend, mas nenhuma tela. O desenho também pede o que o backend não tem:
- a escala de 0 a 10 (recomendação), ao lado da de 1 a 5;
- o comentário opcional;
- a resposta enviada de uma vez (hoje é uma chamada por pergunta, acima do limite de 10 requisições a cada 20 segundos do plano).

Além disso, o RH não tem como criar e encerrar a pesquisa nem ler os resultados.

Os ciclos de avaliação de desempenho (360 por competências) também têm backend, mas o RH não tem tela: não cria ciclo, não muda a situação, não atribui avaliações (hoje é uma chamada por avaliação) e não responde contestações.

## What Changes

- **Escala e comentário** (D1):
  - `pergunta_clima.escala`: concordância (1 a 5) ou recomendação (0 a 10);
  - o contador anônimo aceita notas de 0 a 10;
  - tabela `comentario_clima`, sem pessoa, departamento nem data.
- **Responder** (D2):
  - `minhas_pesquisas_clima` GET: as pesquisas da pessoa, com a situação e as perguntas que faltam;
  - `pesquisas_clima/{id}/responder` POST: todas as notas e o comentário numa chamada, tudo ou nada.
- **RH da pesquisa** (D3):
  - `pesquisas_clima_rh` GET: todas as pesquisas, com a situação, as perguntas e quantas pessoas responderam, no geral e por departamento;
  - o POST da pesquisa aceita as perguntas juntas;
  - incluir pergunta só antes de a pesquisa abrir.
- **Resultados** (D4):
  - cada linha traz a escala e os favoráveis e desfavoráveis;
  - a resposta traz os nomes dos departamentos, quantas pessoas responderam e os comentários (em ordem alfabética, sem id, só com o mínimo atingido).
- **Ciclos de avaliação de desempenho** (D5 a D7):
  - `ciclos_avaliacao_rh` GET: ciclos com contagens (também por autoavaliação e gestor), contestações abertas com nomes, departamentos e pessoas;
  - `ciclos_avaliacao/{id}/avaliacoes` GET;
  - `ciclos_avaliacao/{id}/atribuir` POST: lote de autoavaliação e/ou gestor, com aviso no sino e por e-mail;
  - o status cancela as avaliações em aberto ao concluir ou cancelar o ciclo.
- **Telas** (D8):
  - "Pesquisa de clima" (todos);
  - "Pesquisas de clima" (RH; Figma 249:4645 e 249:4885);
  - aba "Avaliações de desempenho" em "Ciclos de avaliação" (Figma F27 249:5068 e 249:5364), com as contestações e o andamento por departamento.

## Non-goals

- Comparar pesquisas ao longo do tempo (evolução) e exportar resultados.
- Perguntas abertas por pergunta: só um comentário por pesquisa.
- Editar ou apagar pesquisa e ciclo depois de criados.
- Calcular a nota final da avaliação de desempenho a partir das relações: continua valendo a nota de cada avaliação.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: pesquisa de clima com escala de recomendação, comentário anônimo e envio único; gestão dos ciclos de avaliação de desempenho pelo RH.

## Impact

- **Backend:**
  - tabelas alteradas: `pergunta_clima` e `resposta_clima_agregado`;
  - tabela nova: `comentario_clima`;
  - endpoints novos: `minhas_pesquisas_clima`, `pesquisas_clima/{id}/responder`, `pesquisas_clima_rh`, `ciclos_avaliacao_rh`, `ciclos_avaliacao/{id}/avaliacoes` e `ciclos_avaliacao/{id}/atribuir`;
  - endpoints alterados: `pesquisas_clima` POST, `pesquisas_clima/{id}/perguntas`, `pesquisas_clima/{id}/resultados`, `perguntas_clima/{id}/responder` e `ciclos_avaliacao/{id}/status`.
- **Frontend:** `api_client.py`, `clima_modelo.py`, `avaliacao_ciclo_modelo.py`, `pagina_pesquisa_clima.py`, `pagina_pesquisas_clima.py`, `avaliacoes_ciclo_ui.py`, `pagina_ciclos_avaliacao.py`, `app.py` (menu) e `theme.py`.
- **Testes:** `tools/testar_clima_avaliacao.py` e `tools/testar_clima_avaliacao_http.py`.
- **Documentação:** `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md` e a tarefa 48.
