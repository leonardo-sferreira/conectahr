# Feriados no cadastro, no calendário de férias e no espelho (change `ponto-rep-p-e-ferias-clt`, tarefas 7.2 e 7.3)

**Data:** 21/11/2026.

## Carga (tarefa 7.1)

- **Fontes:**
  - Portaria MGI nº 11.460, de 29/12/2025 (DOU de 30/12/2025, seção 1, p. 59), lida no texto: 9 pontos facultativos federais em 2026;
  - Lei estadual de SP nº 9.497/1997: 9 de julho;
  - Lei municipal de São Paulo nº 14.485/2007, art. 10, citada no calendário oficial de 2026 da Prefeitura: 25 de janeiro e Corpus Christi.
- **Conferência:** `python tools/feriados.py` deu 6/6:
  - Páscoa 05/04/2026 e 28/03/2027;
  - Corpus Christi 04/06/2026 e 27/05/2027;
  - as datas móveis batem com a portaria.
- **Carga** (`ConectaHR/semear_feriados`, com a lista de `tools/feriados.py --json`): a primeira rodada criou 12 e pulou 3, que a BrasilAPI já tinha gravado como ponto facultativo nacional; a segunda criou 0.
- **2027:** só os feriados de SP. Os facultativos federais entram quando a portaria de 2027 sair, em dezembro.

## Backend (tarefa 7.2)

- `calendario` GET devolve o feriado inteiro, inclusive `tipo` (feriado ou ponto facultativo) e a abrangência.
- `feriados` POST:
  - aceita `tipo` e `observacao`;
  - exige o estado no feriado estadual, e o estado e o município no municipal;
  - grava a auditoria `criar_feriado`.
- `feriados/{id}` PATCH (novo): edita, desativa ou reativa, com a auditoria `editar_feriado` ou `desativar_feriado`. Não há exclusão.
- Só RH e Admin; os demais perfis recebem 403.
- Antes do push, conferi que o endpoint no ar era igual ao git. O dry-run teve 1 `UPDATE` e 1 `CREATE`, e `checar_endpoints` deu 292, 0 falhas.

## Espelho e calendário (tarefa 7.3)

- **Espelho:** o 9 de julho aparece como "Feriado estadual (SP) — Revolução Constitucionalista", sem falta (`tools/testar_ponto_mensal.py`, 99/99). Também conferidos o rótulo municipal e o nacional.
- **Testes relacionados:** `testar_ponto` 41/41, `testar_folha_ponto` 46/46 e `testar_ferias` 93/93.

## Prints (prévia sem rede, dados fictícios) e Figma

| Tela | Streamlit | Figma |
|---|---|---|
| Férias, calendário do mês (julho/2026: 9 de julho estadual, férias aprovadas de 20 a 29) | `frontend-feriados/ferias-calendario-julho.png` | `frontend-feriados/figma-466-833-calendario.png` (466:833) |
| Estrutura da empresa, aba "Feriados" (tipo e abrangência) | `frontend-feriados/estrutura-feriados.png` | `frontend-feriados/figma-468-838-feriados.png` (468:838) |

O calendário segue o componente do Figma: grade de domingo a sábado, marcações de feriado e de ponto facultativo, férias aprovadas e em análise, legenda e a nota "Feriado e ponto facultativo são dias sem expediente". Em volta dele, a página segue a tela Férias já implementada, com os cartões de saldo, períodos e dias vendidos e o botão "Ver calendário". Ela não tem o formulário ao lado, como no 466:833, porque o pedido continua no modal "Solicitar férias".
