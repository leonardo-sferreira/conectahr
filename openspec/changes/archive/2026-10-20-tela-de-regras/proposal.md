# Proposal

## Why

A tela Regras (Figma 287:884, simulação 288:886 e os modais 288:1186 a 288:1391; tarefas 36 e 37 de `concluir-frontend-streamlit`) ainda não existe no Streamlit, e o usuário pediu (20/10/2026) que seja feita. O backend tem instrumentos normativos e regras de override, com aprovação, versões e simulação, mas faltam peças que o desenho pressupõe: rejeitar uma regra de override, mudar a prioridade, apontar conflito entre regras e impedir que uma regra em conflito seja publicada.

## What Changes

- **Função `ConectaHR/impacto_override`** (D1): as pessoas atingidas por uma regra (a lógica que hoje está dentro da simulação) e os conflitos com regras vigentes.
- **Simulação** (`regras_override/{id}/simular`, D2): passa a usar a função e a devolver os conflitos, o número de departamentos e o valor da matriz do contrato quando nenhuma regra se aplica (antes vinha nulo).
- **Conflito bloqueia** (D3): `enviar_aprovacao` e `aprovar` recusam uma regra com conflito; a lista marca as regras em rascunho ou pendentes que têm conflito.
- **Novos endpoints** (D4): `regras_override/{id}/rejeitar` (com motivo) e `regras_override/{id}/prioridade` (só rascunho ou pendente). `aprovar` aceita uma justificativa opcional, que vai para a auditoria.
- **Tela Regras e Conformidade** (D5): filtros (todos, pendentes, com conflito, vigentes), instrumentos e regras com selo e ações, novo instrumento, nova regra, simulação de impacto, aprovar, rejeitar, nova versão e histórico.

## Non-goals

- Suspender e revogar instrumento pela tela (os endpoints existem, mas o Figma não desenha).
- "Aprovar" e "Aplicar" como dois passos: no backend, aprovar já deixa a regra vigente (com a versão anterior encerrada). A tela usa um passo só (D5).
- Corrigir o `resolver_regra` (usa `||` no `where` para `data_fim`); fica registrado como risco.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: conflito entre regras de override bloqueia o envio e a aprovação; rejeição e prioridade da regra; tela de regras.

## Impact

- Backend: função `impacto_override`; `regras_override/{id}/simular`, `enviar_aprovacao`, `aprovar` e `regras_override` GET alterados; `regras_override/{id}/rejeitar` e `/prioridade` novos.
- Frontend: `api_client.py`, `regras_modelo.py`, `pagina_regras.py`, menu.
- Testes: `tools/testar_regras.py` e `tools/testar_regras_http.py`.
- Documentação: `docs/regras-de-negocio.md`, `docs/figma-pendencias.md`, tarefas 36 e 37.
