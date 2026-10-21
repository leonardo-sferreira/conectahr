# F17 — Consulta e cancelamento de delegações

## Why

O menu Delegações ainda está em construção. O usuário autorizou somente a parte suportada
pelos contratos atuais, sem alterar Xano nem a Central de Pendências.

## What Changes

- Página do Gestor com delegações concedidas/recebidas, abas e estados derivados das datas.
- Cancelamento pelo titular, com autorização final no endpoint existente.
- Criação indisponível: falta catálogo autorizado de substitutos com IDs de usuário.
- Informação honesta sobre escopos e filas; sem simular transferência de permissões.
- Testes, documentação e evidências locais, mantendo o F17 completo pendente.

## Capabilities

### New Capabilities

Nenhuma capability separada.

### Modified Capabilities

- `conectahr`: apresentação parcial de delegações do Gestor.

## Impact

Frontend, testes e documentação. Somente `GET minhas_delegacoes` e
`POST delegacoes/{id}/cancelar`. `POST delegacoes` não será chamado. Sem alteração de backend,
Central, dados de teste reais, permissões ou configurações locais do MCP.
