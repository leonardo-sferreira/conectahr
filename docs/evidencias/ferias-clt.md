# Férias pela CLT (change `ponto-rep-p-e-ferias-clt`, tarefas 6.1 a 6.3)

**Data:** 13/10/2026. **Como:** funções rodadas no Xano pela CLI (`xano function run`). As regras do pedido foram
testadas em `ConectaHR/validar_pedido_ferias` com situações simuladas (sem criar pedidos no banco); a situação real
foi lida de uma ficha de teste, só com números e datas.

## Situação (`ConectaHR/situacao_ferias`)

| Cenário | Esperado | Obtido |
|---|---|---|
| Ficha CLT admitida em 01/03/2025, data 01/12/2026 | Janela 01/03/2026 a 01/03/2027, direito 30, saldo 30 | Igual |
| A mesma ficha em 01/12/2025 (antes de 12 meses, regra proporcional) | Direito proporcional: 22 dias | Igual |
| Primeira versão, sem parênteses em `$regra != null && ...` | — | `proporcional` vinha nulo; corrigido com parênteses em cada comparação (regra do `xano-workspace/AGENTS.md`) |

## Matriz CLT (`ConectaHR/ajustar_regras_ferias_clt`)

| Cenário | Esperado | Obtido |
|---|---|---|
| Primeira execução | Antecedência 30 → 45, mínimo dos outros períodos vazio → 5, venda vazio → 10 | `alterada: true` |
| Segunda execução | Nada muda | `alterada: false` |

## Regras do pedido (`ConectaHR/validar_pedido_ferias`)

Situação CLT simulada: saldo 30, antecedência 45, até 3 períodos, mínimo 5, um de 14, venda até 10. Hoje: 13/10/2026.

| Cenário | Esperado | Obtido |
|---|---|---|
| 30 dias de uma vez (início numa terça) | Aceito, restam 0 | Igual |
| Spec: início daqui a 30 dias | "pelo menos 45 dias de antecedencia" | Igual |
| Spec: período de 4 dias | "pelo menos 5 dias" | Igual |
| Spec: vende 10 e pede 5 | Aceito, restam 15 | Igual |
| Spec: pede 27 com saldo 30 | "Sobrariam 3 dias…" | Igual |
| Spec: vende 11 | "no maximo 10 dias" | Igual |
| Spec: começa em 23/12 (Natal em 25/12) | "dois dias antes de um feriado…" | Igual |
| Começa numa sexta e num sábado | Recusado (descanso semanal) | Igual |
| 5 dias sem nenhum de 14, sobram 25 | Aceito | Igual |
| Segundo período de 5, sem 14, sobrariam 10 | "Um dos periodos precisa ter pelo menos 14 dias…" | Igual |
| Depois de vender 10, um período de 15 | Aceito | Igual |
| Segunda venda no mesmo período aquisitivo | "A venda de dias ja foi feita…" | Igual |
| Terceiro período deixando sobra | "…ja seria o ultimo periodo permitido" | Igual |
| Quarto período | "numero maximo de periodos" | Igual |
| Saldo insuficiente | "Saldo insuficiente: restam 10 dias…" | Igual |
| Antes de 12 meses sem proporcional | "ainda nao completou o periodo aquisitivo" | Igual |
| Antes de 12 meses com proporcional (22 dias) | Aceito | Igual |
| Estágio vendendo 5 dias | "nao permite vender dias" | Igual |
| Quantidade de dias diferente das datas | "nao confere com as datas" | Igual |

`tools/testar_ferias.py`: 64/64 (tela com saldo, períodos, venda e as mesmas regras antes de enviar).

## Não verificado

- `ferias/solicitacoes` POST e `minha_situacao_ferias` GET por HTTP com login (código por e-mail). As duas chamam as
  funções testadas acima.
- Prints com o Figma da seção 22: o MCP do Figma está desconectado (o Figma ficou para depois, por decisão do usuário).
