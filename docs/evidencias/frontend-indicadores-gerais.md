# Indicadores gerais (F33; tarefa 49 da change `concluir-frontend-streamlit`)

**Data:** 21/11/2026. **Figma:** [249:7492](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=249-7492).

## O que entrou

- **Página "Indicadores gerais"** no menu Admin, que antes listava o item sem página
  (`frontend/pagina_indicadores_gerais.py` e `indicadores_gerais_modelo.py`). Usa o `indicadores` GET que já existia (RH e
  Admin), sem mudança no backend.
  - Quatro números: headcount, turnover, absenteísmo e eNPS.
  - Admissões e desligamentos por trimestre, com uma consulta por trimestre.
  - Headcount por departamento, agrupando o resto em "Outros".
  - Horas extras do período.
  - Período de 3, 6 ou 12 meses.
  - "Exportar CSV" por `indicadores/exportar_csv`, que o backend registra na auditoria.
- Abaixo do mínimo de pessoas do backend, os totais aparecem como "Oculto", nunca como zero.

## Testes

| Teste | Resultado |
|---|---|
| `python tools/testar_indicadores_gerais.py` | 19/19 |
| `testar_indicadores_equipe` (usa as mesmas colunas), `testar_menu`, `medir_contraste` | OK, 12/12, 0 pares |

Print com API simulada e dados fictícios: [`frontend-indicadores-gerais/1-indicadores-gerais.png`](frontend-indicadores-gerais/),
ao lado do Figma (`figma-249-7492.png`).

Diferenças do Figma, por falta de dado no backend:
- o eNPS aparece como "—", porque não há pesquisa de eNPS;
- não há filtro por departamento, porque o cálculo é da empresa toda;
- não há "Departamento com mais horas".

**HTTP com login (21/11/2026):** `indicadores` GET de 01/12/2025 a 21/11/2026: Admin 200 com `turnover` e
`distribuicao_departamento` (headcount 9, totais não ocultos); Colaborador 403; Gestor 403 (conta promovida só durante o
teste); `indicadores/exportar_csv`: Admin 200 com CSV não vazio.
