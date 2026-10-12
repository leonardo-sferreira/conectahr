# Evidências — Tela de ponto no REP-P (change ponto-rep-p-e-ferias-clt, grupo 4)

Telas construídas em 12/10/2026 no frontend Streamlit, a partir da seção 21 do Figma ("Ponto REP-P"). O ponto segue a
Portaria MTP nº 671/2021: marcação sem ordem nem limite (art. 74), comprovante de cada marcação (arts. 79 e 80),
tratamento sem alterar a marcação original (art. 82) e espelho do mês com o cabeçalho do art. 84. Não há mais a visão
semanal.

| Nó do Figma | O que é | Código |
|---|---|---|
| 463:825 | Hoje: relógio, "Marcar ponto", marcações do dia com NSR e comprovante, comprovantes das últimas 48 horas | `frontend/pagina_ponto.py` |
| 464:826 | Mês: cabeçalho do art. 84, resumo e a planilha do mês; correção pela seleção da linha | `frontend/pagina_ponto.py`, `frontend/planilha_ponto.py` |
| 465:830 | Comprovante de Registro de Ponto do Trabalhador (PDF) | `frontend/comprovante_ponto.py` |
| 465:856 e 465:894 | Pedido de correção: incluir uma marcação ou desconsiderar uma | `frontend/planilha_ponto.py` |
| 465:932 | Estados: carregando, vazio, sucesso, erro, bloqueado e permissão negada | `frontend/pagina_ponto.py` |
| 468:1458 | Seção 21 no escuro | `frontend/theme.py` (`_ESCURO_CSS`) |

As regras ficam em `frontend/ponto_modelo.py` (Hoje), `frontend/ponto_mensal_modelo.py` (mês, cabeçalho e CSV) e
`frontend/folha_modelo.py` (folha da equipe), sem Streamlit.

**Endpoints usados.** Os do colaborador não recebem id: usam só o token.
- `meu_ponto` (GET): o resumo de cada dia, as marcações da ARP com NSR e os tratamentos;
- `ponto/marcar` (POST): grava a marcação e devolve os dados do comprovante;
- `ponto/comprovantes` (GET): marcações dos últimos 7 dias, empregador e trabalhador. Agora também traz a admissão, o
  cargo e a jornada da regra do contrato, para o cabeçalho do espelho;
- `ponto/correcao` (POST): pedido de inclusão ou de desconsideração;
- `folha_ponto/mes` e `folha_ponto/tratar` (folha da equipe): marcações sem CPF nem hash e o ajuste direto como tratamento.

`ponto/correcao` e `folha_ponto/tratar` passaram a guardar em `valor_original` o horário da marcação a desconsiderar.
Assim, a Central de Pendências mostra o dia e a hora também nesse tipo de pedido.

## Diferenças em relação ao Figma

- **Horário contratual.** O cadastro não guarda horários de entrada e saída, só a duração da jornada na regra do
  contrato. Por isso o cabeçalho mostra "8h48 por dia · 44h00 por semana · intervalo de 1h00" no lugar de
  "08:00–12:00 e 13:00–17:48".
- **Planilha no modo claro.** O `st.dataframe` desenha num canvas com as cores do tema base do Streamlit, que é
  escuro. No modo claro, a planilha recebe o filtro `invert(1) hue-rotate(180deg)`, e as cores das células já vão
  ajustadas para sair certas depois dele (`estilo_planilha_ponto` em `theme.py`). A caixa de seleção da linha fica
  num âmbar mais escuro que o do Figma.
- **Seleção da linha.** O dia é escolhido pela caixa de seleção do próprio `st.dataframe` (design D8).

## Como repetir

```
python tools/testar_comprovante.py    # 18 verificações (PDF do comprovante, art. 79)
python tools/testar_ponto.py          # 35 verificações (Hoje, estados, ausência)
python tools/testar_ponto_mensal.py   # 58 verificações (mês, admissão, art. 84, CSV, pedido de correção)
python tools/testar_folha_ponto.py    # 40 verificações (folha da equipe com tratamentos e ajuste)
python tools/testar_decisoes.py       # 62 verificações (Central, com os pedidos do REP-P)
```

Rodam sem rede, com uma API simulada (dados fictícios). **Resultado em 12/10/2026: todos passando.** As demais suítes
de `tools/` também passaram (benefícios, cadastro, conferência de documentos, férias, login, onboarding, pagamento,
perfil, privacidade, REP-P e solicitações).

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Hoje: título, relógio com segundos, as marcações em ordem, com o papel de cada uma ("Entrada", "Saída para o almoço", "Volta do almoço", "Saída"; num dia com mais, "Saída para intervalo" e "Volta do intervalo"), a hora e o NSR de 9 dígitos | ok |
| Sucesso | Três marcações seguidas, todas gravadas: sem ordem nem limite (art. 74) | ok |
| Sucesso | Depois de marcar: "Ponto marcado às 00:09:22 (UTC-03:00). NSR …" e o comprovante na hora | ok |
| Sucesso | Comprovante em PDF de cada marcação de hoje e das últimas 48 horas | ok |
| Sucesso | PDF com título, NSR, empregador e CNPJ, local, nome e CPF, data e hora com fuso, INPI e hash | ok |
| Sucesso | Mês: todos os dias, em pares "Ent. 1", "Saí. 1"…; a 5ª marcação abre o 3º par | ok |
| Sucesso | Incluída aparece como "18:05 (I)"; desconsiderada vai para a coluna própria como "08:01 (D)"; tratamento desfeito não vale | ok |
| Sucesso | Situações: completo, ajustado, incompleto (com "corrigir"), hoje em jornada, férias, atestado, ausência em análise, falta injustificada, feriado e ponto facultativo pelo nome, folga, sem registro | ok |
| Sucesso | Tratamento com marcação sem par: INCOMPLETO, não AJUSTADO, para a saída que falta não sumir (desde 12/10/2026) | ok |
| Sucesso | Admissão em 15/10: dias 1 a 14 em branco, sem situação e sem falta; dias futuros em branco | ok |
| Sucesso | Cabeçalho do art. 84 (empregador, CNPJ, local, trabalhador, CPF, admissão, cargo, horário contratual, emissão e período), na tela e no CSV | ok |
| Sucesso | CSV com BOM e ";", cabeçalho, planilha, observação, NSR de cada marcação e a legenda | ok |
| Sucesso | Pedido pela seleção da linha: inclusão com o horário de Brasília; desconsideração só das marcações sem pedido em análise | ok |
| Sucesso | Folha da equipe: marcações e tratamentos na mesma planilha; ajuste direto como inclusão ou desconsideração; pedidos pendentes descritos pelo tipo | ok |
| Sucesso | Central: "Incluir marcação" e "Desconsiderar marcação" com o dia e o horário | ok |
| Vazio | "Você ainda não marcou o ponto hoje." e "Nenhuma marcação nas últimas 48 horas." | ok |
| Erro | Antes da admissão: a mensagem do backend e "Nada foi gravado." | ok |
| Erro | Recusa do backend no modal do pedido, que continua aberto | ok |
| Bloqueado | Empregador não cadastrado: aviso para o RH cadastrar em "Ponto eletrônico (REP-P)" | ok |
| Permissão negada | Comprovantes com 403: "Cada pessoa vê só os próprios." | ok |
| Permissão negada | Própria folha na folha da equipe: só consulta, sem "Ajustar o dia" | ok |
| Carregando | Spinner enquanto o ponto carrega | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-ponto-rep-p/`](frontend-ponto-rep-p/), para pôr lado a lado com os nós do
Figma:

| Print | Figma |
|---|---|
| `1-hoje` | 463:825 |
| `2-hoje-depois-de-marcar` | 465:932 (sucesso) |
| `3-mes` | 464:826 |
| `4-pedido-inclusao` | 465:856 |
| `5-pedido-desconsideracao` | 465:894 |
| `6-folha-equipe` | folha da equipe com a planilha do REP-P |
| `7-hoje-escuro` e `8-mes-escuro` | 468:1458 |
| `9-folha-ajuste` | ajuste direto como tratamento |

## Endpoints antigos desativados

Desde 12/10/2026, `ponto/{id}/solicitar_correcao`, `ponto/solicitar_correcao_dia` e `folha_ponto/ajustar` só
recusam o pedido (400) e indicam o caminho novo (`ponto/correcao` e `folha_ponto/tratar`). Eles gravavam o horário
direto no registro do dia, sem passar pela ARP, o que o REP-P não permite. Até este frontend ir ao ar, o app publicado
mostra essa mensagem a quem tentar pedir correção pela tela antiga.
