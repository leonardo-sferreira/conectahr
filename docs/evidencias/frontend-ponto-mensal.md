# Evidências — espelho de ponto mensal e correção de qualquer dia (tarefa 78)

O colaborador já marcava ponto e via a semana. Faltava consultar os registros mês a mês, com as marcações e a
situação de cada dia, e pedir correção de qualquer dia, **inclusive de um dia sem nenhuma marcação**, que antes
era impossível. O fluxo completo, caso a caso, está em [`docs/fluxos/ponto-mensal.md`](../fluxos/ponto-mensal.md).

> **A conferir com o Figma.** O Figma estava fora do ar. A visão mensal reaproveita o espelho da semana (39:18) e o
> modal "Solicitar correção de ponto" (221:196). Precisa ser desenhada no Figma quando a conexão voltar.

## Backend: o que mudou e como foi conferido

- **`ponto/solicitar_correcao_dia` (POST, novo).** Pede a correção de um dia passado sem nenhuma marcação. Cria o
  registro do dia (Incompleto, sem marcações) e o pedido. Regras:
  - só o próprio colaborador, não desligado;
  - só dia passado no horário de Brasília, não anterior à admissão e sem registro já existente;
  - o horário respeita a janela do dia e não pode ser no futuro.
- **`ponto/{id}/solicitar_correcao` (POST), reforçado** com três conferências:
  - o horário pedido precisa ser do dia do registro: da meia-noite UTC até as 06:00 (Brasília) do dia seguinte, o que
    cobre a virada de data da tarefa 73;
  - não pode ser no futuro;
  - respeita a ordem das marcações que já existem. Antes, uma saída antes da entrada passava e gerava horas negativas.
- **Como foi publicado e conferido:**
  - `checar_endpoints.py` nos arquivos locais: grupo Ponto sem falhas;
  - `--dry-run` mostrou só as duas mudanças (1 criada, 1 atualizada), e o `push` publicou as duas;
  - o `pull` seguinte trouxe as duas;
  - por HTTP, sem token e com token inválido, a resposta foi 401;
  - `checar_endpoints.py` depois do push: 187 endpoints, nenhuma falha.
- **O que não foi testado:** não houve teste com conta real, porque o login pede código por e-mail.

## Como repetir

```
python tools/testar_ponto_mensal.py   # 29 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 11/10/2026: 29 de 29.** `testar_ponto.py` continua com 36 de 36, e o resto da bateria também passa.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Do dia da admissão até hoje; dias futuros fora | ok |
| Sucesso | Registro completo; registro aberto de dia passado vira incompleto | ok |
| Sucesso | Folga (fim de semana) e feriado nacional com correção para quem trabalhou | ok |
| Sucesso | Dia útil sem nada: "Sem registro", com correção ou ausência | ok |
| Sucesso | Ausência aprovada: justificado; ausência pendente: em análise; recusada não justifica | ok |
| Sucesso | Férias aprovadas aparecem; férias só pedidas não contam | ok |
| Sucesso | Correção pendente: aviso e o campo sai do pedido; as quatro em análise: sem botão | ok |
| Sucesso | Correção recusada: mostra o motivo | ok |
| Sucesso | Resumo do mês, meses disponíveis (até 24) e CSV com BOM e ";" | ok |
| Sucesso | Dia sem registro: pede pelo endpoint novo, com a data e o horário de Brasília | ok |
| Sucesso | Dia com registro: pede pelo endpoint do registro, sem a marcação já em análise | ok |
| Erro | Recusa do backend no modal, que continua aberto | ok |
| Erro | Sem o calendário (feriados), o mês aparece do mesmo jeito | ok |
| Vazio | "Nenhum dia neste mês ainda." | ok |
| Carregando | Spinner enquanto o ponto carrega | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-ponto-mensal/`](frontend-ponto-mensal/): `1-espelho-mensal`,
`2-corrigir-dia-sem-registro` e, no tema escuro, `3` e `4`.
