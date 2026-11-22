# Estrutura da empresa e Auditoria só do Admin

**Data:** 22/11/2026. **PR:** #131. Pedido do dono do produto: as duas telas são opções do Admin, não do RH.

## Testes por HTTP (Xano real, contas de teste Admin, RH e Colaborador)

18 de 18 verificações. Nenhuma gravação: o RH tenta e recebe 403; o Admin só lê.

| Caso | Esperado | Obtido |
|---|---|---|
| Admin lê a trilha de auditoria | 200 | ok |
| RH lê a trilha sem filtro, ou com outra ação | 403 | ok |
| RH lê só as execuções da rotina diária (tela Rotina diária) | 200, só `processar_rotinas_diarias` | ok |
| Colaborador, mesmo com o filtro da rotina | 403 | ok |
| RH lê departamentos e cargos (cadastro de colaboradores) | 200 | ok |
| RH cria ou edita departamento, muda a situação do departamento, cria cargo e nível, importa feriados | 403 | ok |
| RH ou Colaborador edita feriado (antes, sem conferência de perfil) | 403 | ok |

Testes sem rede: `testar_menu`, `testar_auditoria`, `testar_departamentos`, `testar_cargos`, `testar_organograma`, `testar_ferias` e `testar_rotina_sessoes` passam, com os casos do RH recusado.
