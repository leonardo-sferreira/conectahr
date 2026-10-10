# Evidências — Pagamento (tarefas 29 e 30)

Tela construída em 10/10/2026 no frontend Streamlit, a partir do Figma (área do colaborador e seção 9, do RH).

| Nó do Figma | O que é | Código |
|---|---|---|
| 70:46 | Pagamento do colaborador: holerites por ano e informes de rendimentos | `frontend/pagina_pagamento.py` |
| 236:357 | RH: "Pagamento — lançamentos", aba Holerites | idem |
| 236:594 | RH: aba Informes de rendimentos | idem |
| 237:363 e 237:402 | Modais "Lançar holerite" e "Lançar informe" | idem |
| 237:441 | Modal "Substituir documento" | idem |

As regras de apresentação ficam em `frontend/pagamento_modelo.py` (sem Streamlit). Não houve mudança no backend.

**Endpoints usados**
- colaborador: `meus_documentos` (só os documentos dele) e `documentos/{id}/arquivo` ("Baixar", que só o dono, o
  RH e o Admin abrem, e audita cada abertura);
- RH e Admin: `documentos_rh`, `organograma` e `documentos` (POST) com `tipo` `holerite` ou `informe_rendimentos`.
  O backend só aceita esses tipos de RH e Admin. O documento nasce aprovado e sem validade. Substituir é o mesmo
  POST com `documento_substituido_id`, e o anterior fica "substituído".

## Como repetir

```
python tools/testar_pagamento.py   # 40 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 40 de 40.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Só o dono (30) | O colaborador usa `meus_documentos`, que só devolve os documentos dele, e nunca a lista do RH | ok |
| Sucesso | Holerites do ano escolhido e informes; o substituído some e fica só a versão nova | ok |
| Sucesso | "Baixar" pede o link ao backend e mostra "Abrir arquivo" | ok |
| Sucesso | Documento cadastral não aparece em Pagamento, e holerite e informe não aparecem em Documentos | ok |
| Sucesso | RH: quem já tem e quem falta na competência, com quem falta primeiro; filtro de departamento; o Admin também lança | ok |
| Sucesso | "Lançar →" abre com a pessoa escolhida e envia colaborador, tipo, nome com a competência e link | ok |
| Sucesso | Informe: lança o do ano-calendário anterior | ok |
| Sucesso | "Substituir" envia o documento substituído e o motivo | ok |
| Só RH (30) | O backend recusa o lançamento de quem não é RH ou Admin: a mensagem aparece no modal, que continua aberto | ok |
| Erro | Antes de enviar, a tela recusa: sem colaborador, link sem https, emissão futura, substituir sem motivo. A API não é chamada | ok |
| Erro | Recusa ao baixar vira alerta; erro ao carregar (colaborador e RH) vira alerta | ok |
| Vazio | Sem holerites e sem informes; conta sem colaborador | ok |
| Carregando | Spinner enquanto os documentos carregam | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-pagamento/`](frontend-pagamento/):

| Print | Compare com |
|---|---|
| `1-pagamento-colaborador` e `2-baixar` | 70:46 |
| `3-rh-holerites` | 236:357 |
| `4-lancar-holerite` | 237:363 |
| `5-substituir` | 237:441 |
| `6-rh-informes` | 236:594 |
| `7-pagamento-escuro`, `8-rh-escuro` e `9-lancar-escuro` | tema escuro (`frontend/theme.py`, `_ESCURO_CSS`) |

## Decisões e diferenças em relação ao Figma

- **Link no lugar do upload.** O arquivo entra por link https de um domínio aprovado, como em Documentos, porque o
  plano do Xano não recebe arquivo.
- **Competência no nome.** O documento não tem campo de competência. A tela grava a competência no nome
  ("Holerite — Agosto/2026", "Informe de rendimentos 2025") e, se o nome não seguir esse padrão, usa a data de
  emissão (holerite: o mês anterior; informe: o ano anterior).
- **Pagamento separado de Documentos.** Holerite e informe saem da tela Documentos e ficam só em Pagamento.
