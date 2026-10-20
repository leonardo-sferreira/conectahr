# Proposal

## Why

O fluxo de desligamento (tarefa 54 de `concluir-frontend-streamlit`; Figma "Pedir desligamento" 224:4056 e "RH — Desligamentos" 249:3075) tem backend, mas nenhuma tela, e o usuário pediu (20/10/2026) que seja feito. O desenho do RH tem um checklist de saída que o backend não guarda (o próprio Figma anota isso), a lista do RH exige um status por chamada (os indicadores e as abas custariam quatro chamadas, acima do limite do plano) e o pedido é recusado para quem tem perfil RH ou Admin, que também são funcionários.

## What Changes

- **Checklist de saída** (D1): tabela `desligamento_checklist`; os itens padrão nascem na aprovação; o RH marca cada um como feito; concluir um desligamento agendado exige todos feitos.
- **Lista do RH** (D2): `solicitacoes_desligamento` GET com o status opcional, as contagens por status e os nomes (pessoa, departamento, cargo, quem pediu e o responsável do RH); o detalhe traz o checklist.
- **Pedido** (D3): qualquer pessoa com ficha pede o próprio desligamento, qualquer que seja o perfil; o gestor do departamento continua podendo pedir o de alguém da equipe; cancelar e consultar os próprios seguem a mesma regra.
- **Telas** (D4): "Pedir desligamento" (a pessoa: pedido, como funciona e os próprios pedidos com cancelar) e "Desligamentos" (RH: indicadores, abas, origem, assumir análise, aprovar, rejeitar, concluir e o checklist).

## Non-goals

- Admin decidindo desligamento: os endpoints de decisão continuam só do RH (como hoje).
- Conclusão automática na data efetiva (o plano não tem tarefas agendadas; a conclusão continua manual).
- Cálculo de verbas rescisórias: o checklist só registra que foi feito.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: checklist de saída do desligamento e pedido por qualquer perfil com ficha.

## Impact

- Backend: tabela `desligamento_checklist`; `solicitacoes_desligamento` GET, `{id}` GET, `aprovar`, `concluir`, POST, `minhas_solicitacoes_desligamento` e `cancelar` alterados; `solicitacoes_desligamento/{id}/checklist/{item_id}` POST novo.
- Frontend: `api_client.py`, `desligamento_modelo.py`, `pagina_pedir_desligamento.py`, `pagina_desligamentos.py`, menu e Perfil (o caminho para pedir).
- Testes: `tools/testar_desligamento.py` e `tools/testar_desligamento_http.py`.
- Documentação: `docs/regras-de-negocio.md` (seção 6), `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`, tarefa 54.
