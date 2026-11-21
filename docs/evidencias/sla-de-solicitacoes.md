# SLA de solicitações (change `sla-de-solicitacoes`)

**Data:** 20/11/2026. **Ambiente:** Xano da equipe (workspace 147338). As contas de teste são da equipe e não aparecem aqui. Os pedidos de teste trazem "TESTE" no texto.

## Horas úteis (`ConectaHR/somar_horas_uteis`, pela CLI do Xano)

| Início (horário de São Paulo) | Horas | Esperado | Obtido |
|---|---|---|---|
| Segunda, 23/11, 10h | 72 | Quinta, 26/11, 10h | Quinta, 26/11, 10:00 |
| Sexta, 27/11, 10h | 72 | Quarta, 02/12, 10h | Quarta, 02/12, 10:00 |
| Sábado, 28/11, 15h | 72 | Quinta, 03/12, 00h (o fim da quarta) | Quinta, 03/12, 00:00 |
| Segunda, 23/11, 10h | 24 | Terça, 24/11, 10h | Terça, 24/11, 10:00 |
| Sexta, 30/10, 10h (feriado na segunda, 02/11) | 24 | Terça, 03/11, 10h | Terça, 03/11, 10:00 |
| Quinta, 19/11, 10h (feriado na sexta, 20/11) | 24 | Segunda, 23/11, 10h | Segunda, 23/11, 10:00 |

`ConectaHR/prazo_sla` sem configuração: setor `rh`, 72 horas, alerta em 57.

## Configuração e prazo com login (19/19)

Contas Admin, RH e Colaborador. A conta de Colaborador virou Gestor só durante o teste.

| Cenário | Esperado | Obtido |
|---|---|---|
| Admin lê `sla_config` | 10 tipos, pode editar | Igual |
| RH e Gestor leem | 10 tipos, sem editar | Igual |
| Colaborador lê | 403 | 403 |
| RH e Gestor gravam | 403 | 403 e 403 |
| 0 e 721 horas; LGPD com 241; tipo inválido | 400 | 400 em todos |
| Pedido "Outra" sem configuração | 72 horas; prazo e alerta (57 horas) pela regra, recalculada no teste a partir da tabela de feriados | Igual; "no prazo" |
| Pedido LGPD | Prazo até o fim do `prazo_resposta` | Igual |
| Desligamento antes da mudança | 72 horas | 72 |
| Admin grava 24 horas para Desligamento | Linha alterada, com quem alterou | Igual |
| Desligamento depois da mudança | 24 horas, 1 dia útil | Igual; o pedido antigo manteve o prazo |
| Fim do teste | Desligamento e "Outra" de volta ao padrão; pedidos de desligamento cancelados | Igual |

## Telas

`tools/testar_sla.py`: 22/22. Cobre a situação, o selo, a ordem, as linhas da configuração e a validação, a aba com Admin, RH, Gestor e Colaborador, o vazio, o erro, a recusa no modal e a fila da Central com o vencido no topo. Os 36 passos de teste do CI passam.

## Pendente

- **3.3, pedido vencido no topo da `central_de_tarefas`:** um pedido "Outra" com SLA de 1 hora útil foi aberto em 20/11. Como esse dia é feriado e cai numa sexta, o prazo é segunda, 23/11, às 01:00. A conferência da Central precisa de um pedido que entre nela, como um desligamento.
- **2.5, aviso `prazo_vencendo`:** rodar a rotina diária duas vezes, depois do alerta, e conferir que avisa uma vez só.
