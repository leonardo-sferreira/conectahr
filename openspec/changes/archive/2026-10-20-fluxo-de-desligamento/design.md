# Design

## Context

Ver proposal.md. Estados: `pendente` → (`iniciar_analise`, RH) `em_analise` → (`aprovar` com data efetiva e motivo) `agendado` (aviso prévio) ou `concluido` (imediato, que já desativa a conta), ou (`rejeitar`) `rejeitada`; `pendente` → (`cancelar`, quem pediu) `cancelada`; `agendado` → (`concluir`, RH, na data efetiva ou depois) `concluido`. Ninguém decide o próprio pedido. As decisões são só do RH.

## Decisions

### D1. Checklist de saída

- Tabela `desligamento_checklist` (`solicitacao_desligamento_id`, `titulo`, `responsavel` (área), `ordem`, `feito`, `feito_em`, `feito_por_user_id`).
- `aprovar` cria os itens padrão (os do Figma): Devolução de equipamentos (TI), Revogar acessos aos sistemas (TI), Entrevista de desligamento (RH), Cálculo das verbas rescisórias (Financeiro).
- `solicitacoes_desligamento/{id}/checklist/{item_id}` POST com `feito` (verdadeiro ou falso): só RH, só com o pedido `agendado` ou `concluido`; ninguém marca o checklist do próprio desligamento; auditado.
- `concluir` exige todos os itens feitos ("Faltam N itens do checklist de saída"). O desligamento imediato já nasce concluído, e o checklist fica para ser cumprido depois.

### D2. Lista do RH

`solicitacoes_desligamento` GET: `status` opcional (vazio = todos). Sem `||` no `where`: com status, a consulta filtra por ele; sem, traz todos. Devolve `contagens` (por status, e concluídos no ano) e, em cada pedido, `colaborador_nome`, `departamento`, `cargo`, `solicitante_nome` e `responsavel_rh_nome`. O detalhe (`{id}` GET) passa a trazer o `checklist`.

### D3. Quem pede

- POST: o próprio desligamento, para qualquer perfil com ficha ativa; o de outra pessoa, só o gestor do departamento dela (`departamento.gestor_colaborador_id`), qualquer que seja o perfil. `origem` = `gestor` quando é de outra pessoa.
- `minhas_solicitacoes_desligamento` e `cancelar`: sem a restrição de perfil (continua valendo "só quem criou cancela" e "só pendente").
- O formulário do Figma tem só data, motivo e comentário: a tela manda `aviso_previo` com os dias até a data (ou `imediato` com 0 se a data for hoje) e monta o motivo do backend (mínimo 5 caracteres) com o motivo escolhido e o comentário.

### D4. Telas

- "Pedir desligamento" (224:4056): aberta por "Pedir desligamento →" no Perfil (o menu do Figma não tem o item). Formulário, "Como funciona" e, abaixo, "Meus pedidos" com a situação e "Cancelar" no pendente. Quem é gestor de departamento escolhe "Para quem" (você ou alguém da equipe), que o Figma não desenha.
- "Desligamentos" (249:3075, grupo RH): indicadores, abas Pendentes, Em análise, Agendados e Concluídos, filtro de origem, tabela; ações por situação: pendente "Assumir análise"; em análise "Rejeitar" e "Aprovar" (modais com motivo e, na aprovação, a data efetiva); agendado "Concluir" (desligado antes da data ou com checklist incompleto). Ao escolher uma linha agendada ou concluída, o checklist aparece com os itens para marcar. Cartão "Etapas" como no Figma.

## Risks / Trade-offs

- [Pedidos agendados antes desta change não têm checklist] → `concluir` só exige os itens que existirem; sem itens, conclui como antes.
- [Erro de execução do XanoScript] → `tools/testar_desligamento_http.py` com login de verdade.
- [Liberar o pedido para RH e Admin] → a decisão continua com outra pessoa do RH (autoaprovação bloqueada em todos os endpoints de decisão).

## Migration Plan

1) Tabela (`CREATE`); 2) endpoints (`CREATE` e `UPDATE`, conferidos contra o que está no ar). Rollback: publicar as versões do git.
