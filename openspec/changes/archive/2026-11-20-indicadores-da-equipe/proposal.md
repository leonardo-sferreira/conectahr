# F18 — Indicadores da equipe, escopo parcial

## Why

O menu do Gestor ainda mostra Indicadores da equipe em construção. A implementação autorizada
usa somente dados já acessíveis, sem Xano novo nem aproximações para métricas bloqueadas.

## What Changes

- Página F18 com período, cards, série mensal e ausências por tipo no recorte da folha.
- Banco corrente agregado separadamente por departamento gerenciado.
- Absenteísmo, clima/eNPS e exportação auditada indisponíveis.
- Cobertura explícita, proteção de grupos pequenos e falhas isoladas por fonte.
- Testes e evidências locais; F18 completo permanece pendente.

## Capabilities

### New Capabilities

Nenhuma capability separada.

### Modified Capabilities

- `conectahr`: apresentação parcial dos indicadores do Gestor.

## Impact

Frontend, testes e documentação. GET folha_ponto/pessoas, folha_ponto/mes, organograma e
colaboradores/{id}/banco_horas. Sem endpoints administrativos, clima, calendário ou escrita.

