# Proposal

## Why

O usuário pediu (21/10/2026) o termômetro de humor da pesquisa de mercado (prioridade 2), com uma pergunta **a cada 10 dias**. É um dos recursos mais citados pelos usuários da Feedz.

A pesquisa de clima é longa e rara. O termômetro dá ao RH e ao gestor um sinal frequente de como as pessoas estão. Também prepara o terreno para o "risco de saída" (prioridade 4) e complementa a NR-1 (riscos psicossociais).

## What Changes

- **Ciclos de 10 dias** (D1): a partir de 21/10/2026; o backend sabe qual é o ciclo de hoje.
- **Dados anônimos** (D2): só contagens por ciclo, setor e nota, e por ciclo, setor e motivo, sem pessoa, data ou hora. Uma tabela separada guarda só quem já respondeu o ciclo, para não responder duas vezes.
- **Responder** (D3): `humor` GET (o ciclo e se a pessoa já respondeu) e `humor` POST. A nota vai de 1 (muito mal) a 5 (muito bem), e o motivo é opcional, de uma lista fechada.
- **Resultados** (D4): `humor/resultados`. RH e Admin veem tudo, com filtro de departamento; o Gestor vê só os setores que gerencia. Grupo com menos de 5 respostas fica suprimido, inclusive por subtração.
- **Telas** (D5):
  - no Início, o cartão do termômetro enquanto a pessoa não respondeu o ciclo;
  - a tela "Termômetro de humor" no grupo RH e no grupo Equipe.

## Non-goals

- Lembrete por e-mail: o plano não tem tarefas agendadas; o cartão no Início faz o papel.
- Comentário livre: um texto pode identificar a pessoa; o motivo é de uma lista fechada.
- Alerta individual ("fulano está mal"): o termômetro é anônimo.
- Risco de saída: fica para depois (prioridade 4).

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: termômetro de humor anônimo a cada 10 dias, com resultados agregados por setor.

## Impact

- **Backend:**
  - tabelas novas `humor_contagem`, `humor_motivo_contagem` e `humor_participacao`;
  - endpoints novos `humor` GET e POST e `humor/resultados` GET.
- **Frontend:**
  - novos: `humor_modelo.py` e `pagina_termometro_humor.py`;
  - alterados: `api_client.py`, `pagina_inicio.py` e `app.py`.
- **Figma:** seção 23 (563:850): Início com o termômetro (563:853), cartão depois de responder (563:971) e resultados (564:855).
- **Testes:**
  - `tools/testar_termometro_humor.py`;
  - `tools/testar_termometro_humor_http.py`.
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção 22);
  - `docs/lgpd/registro-de-operacoes.md` (F15 e cobertura);
  - `docs/lgpd/retencao.md`;
  - `docs/figma-pendencias.md`.
