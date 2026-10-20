# Proposal

## Why

O usuário pediu (20/10/2026) que cada pessoa da empresa registre as próprias metas num ciclo anual, em três etapas de quatro em quatro meses, todas no mesmo período para todos. Hoje as metas (`meta_avaliacao`) só são criadas pelo RH, uma a uma, e não há formulário, autoavaliação por etapa, janela de preenchimento nem feedback do gestor.

## What Changes

- **Ciclo anual de metas** criado pelo RH, com três janelas (D1): 1) definir as metas (fevereiro), 2) registrar o que foi alcançado e acompanhar (junho), 3) fechamento (outubro). O RH pode ajustar as datas antes de o ciclo abrir. Fora da janela, e depois do envio da etapa, não há edição.
- **Perguntas pré-definidas** mantidas pelo RH (texto, orientação, ordem, ativa), com um conjunto sugerido (D2).
- **Formulário de cada pessoa** (D3), para qualquer conta com ficha de colaborador, seja Colaborador, Gestor, RH ou Admin:
  - etapa 1: a meta de cada pergunta (texto);
  - etapas 2 e 3: o que foi alcançado (texto) e a autoavaliação "Abaixo do esperado", "Dentro do esperado" ou "Acima do esperado";
  - salvar rascunho dentro da janela; enviar fecha a etapa.
- **Feedback por etapa** (D4): o superior direto ou o gestor do departamento da pessoa registra um feedback em cada etapa enviada. Fica numa caixa da etapa, visível para a pessoa, o gestor e o RH.
- **Telas** (D5): bloco "Ciclo de metas" na Trajetória, que leva à tela "Metas do ciclo"; para o RH, "Ciclos de avaliação" (ciclos, perguntas e formulários de todos); para quem tem equipe, "Metas da equipe" (formulários da equipe e o feedback). Ciclos em andamento e finalizados ficam no histórico das três telas.

## Non-goals

- Abrir e fechar etapas por tarefa agendada: as janelas valem pelas datas, sem rotina.
- Aprovação das metas pelo gestor.
- Ligação com a avaliação 360, o PDI e as metas antigas (`meta_avaliacao`), que continuam como estão.
- E-mail na abertura de cada etapa (o plano não tem tarefas agendadas).

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: novo requisito do ciclo anual de metas, com janelas, formulário, autoavaliação, feedback e visibilidade.

## Impact

- Backend: tabelas `ciclo_metas`, `pergunta_meta`, `formulario_meta`, `resposta_meta` e `feedback_meta`; endpoints no grupo Colaboradores (`ciclos_metas`, `perguntas_meta`, `meu_ciclo_metas`, `formularios_meta` e as escritas de resposta, envio e feedback).
- Frontend: `api_client.py`, `ciclo_metas_modelo.py`, `pagina_metas_ciclo.py` (pessoa), `pagina_ciclos_avaliacao.py` (RH), `pagina_metas_equipe.py` (gestor), bloco na Trajetória, menu e sino.
- Testes: `tools/testar_ciclo_metas.py` (AppTest) e `tools/testar_ciclo_metas_http.py` (login de verdade).
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`.
