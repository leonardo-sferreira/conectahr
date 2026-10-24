# Tasks

## 0. Figma

- [x] 0.1 Desenhar a seção 23 (563:850): Início com o termômetro (563:853), cartão depois de responder (563:971) e resultados (564:855) (D5). Verificar: prints dos nós.
  - **Feito (21/10/2026):** modo claro. Falta a versão escura (docs/figma-pendencias.md).

## 1. Backend

- [x] 1.1 Tabelas `humor_contagem`, `humor_motivo_contagem` e `humor_participacao` (D2). Verificar: dry-run só com `CREATE`.
  - **Feito (21/10/2026):** publicadas.
- [x] 1.2 `humor` GET e POST e `humor/resultados` (D1, D3, D4). Verificar: `checar_endpoints`, dry-run só com `CREATE` e a fórmula do ciclo.
  - **Feito (21/10/2026):** publicados; `checar_endpoints` 275, 0 falhas. As expressões publicadas foram conferidas iguais às do git. A fórmula do dia juliano dá o mesmo ciclo que a conta por datas em todos os dias de 2026 a 2030.
- [x] 1.3 Rodar `tools/testar_termometro_humor_http.py` com login (uma conta do RH ou Gestor com ficha; outra de Colaborador, se der).
  - **Feito (23/10/2026):** 15/15 com uma conta do RH/Admin com ficha (a de Colaborador ficou para depois). A primeira rodada deu 500 em `humor/resultados`: as chaves dos mapas tinham `|`, que o Xano lê como filtro. Trocadas por `k{ciclo}_{nota}` (PR #105).

## 2. Frontend

- [x] 2.1 `api_client.py` e `humor_modelo.py`. Verificar: regras em `tools/testar_termometro_humor.py`.
- [x] 2.2 Cartão no Início, "Termômetro de humor" no grupo RH e no grupo Equipe, e o CSS claro e escuro (D5). Verificar: `tools/testar_termometro_humor.py` e prints no Chrome.
  - **Feito (21/10/2026):**
    - testes: 22/22;
    - prints no Chrome nos dois temas.
  - **Junto:** a escala da pesquisa de clima não destacava a nota escolhida. O seletor do CSS usava o atributo `kind`, que o Streamlit 1.64 não põe mais no botão; agora usa `aria-checked`.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 22), `docs/lgpd/registro-de-operacoes.md` (F15 e cobertura), `docs/lgpd/retencao.md` e `docs/figma-pendencias.md`. Verificar: `openspec validate termometro-de-humor`.

## 4. Ajustes pedidos pelo usuário (23/10/2026)

- [x] 4.1 O cartão no Início vai para baixo dos comunicados e acima da FAQ, que fica por último; cada opção ganha um emoji (😣 🙁 😐 🙂 😄) no lugar da bolinha de cor. Verificar: Figma 563:853 atualizado, `tools/testar_termometro_humor.py` (posição) e prints no Chrome nos dois temas.
  - **Feito (23/10/2026):** 23/23. No Figma, os emojis são rostinhos em SVG (o renderizador do Figma não desenha emoji colorido); no app, são os emojis do sistema.
