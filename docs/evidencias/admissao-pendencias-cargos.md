# Admissão com pendências, cargos e níveis de partida (13/10/2026)

**Como:** funções rodadas no Xano pela CLI. As respostas trazem só ids e contagens, sem dado pessoal.

## Pendências de documento (`ConectaHR/gerar_pendencias_obrigatorias`)

| Cenário | Esperado | Obtido |
|---|---|---|
| Simulação para todos os não desligados, excluindo uma conta de teste pelo e-mail | Contar sem gravar | 5 pessoas, 6 a 7 pendências cada (33), 1 excluída |
| Execução real | 33 pendências criadas, com aviso a quem tem conta | 33 criadas, 1 excluída |
| Segunda execução | Nenhuma pendência nova | 0 criadas |
| `colaboradores` POST | Gera as pendências da pessoa admitida | Publicado; por HTTP com login: não verificado (código por e-mail) |

## Níveis e cargos (`ConectaHR/semear_cargos_genericos`)

| Cenário | Esperado | Obtido |
|---|---|---|
| Primeira execução | 9 níveis, os cargos genéricos que não existem e nível nos 3 cargos antigos | 9 níveis, 15 cargos ("Atendente" já existia), 3 cargos com nível |
| Segunda execução | Nada novo | 0, 0 e 0 |

`tools/testar_cadastro.py`: 65/65 (carga horária por contrato e o aviso dos documentos pedidos).
