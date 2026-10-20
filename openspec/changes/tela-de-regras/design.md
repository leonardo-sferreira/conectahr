# Design

## Context

Ver proposal.md. `regras_override/{id}/aprovar` já bloqueia a autoaprovação, encerra a regra vigente do mesmo parâmetro, abrangência e escopo e grava a nova com a versão seguinte. `simular` levanta a população pela abrangência e resolve o valor atual de cada pessoa com `ConectaHR/resolver_regra`, mas devolve `valor_atual` nulo quando a pessoa segue a matriz do contrato. O guia do workspace pede para evitar função chamando função.

## Decisions

### D1. Função `impacto_override`

Entrada: `override_id`. Saída: `override`, `afetados` (pessoas ativas pela abrangência: a mesma lógica da simulação, que sai de lá) e `conflitos`.

**Conflito** = outra regra `vigente` do mesmo `parametro`, com a mesma `prioridade`, `valor_novo` diferente, vigência que se sobrepõe e pelo menos uma pessoa atingida em comum. A pessoa em comum é conferida pessoa a pessoa contra a abrangência da outra regra (empresa, estado, município, tipo de contrato, departamento, cargo ou colaborador), sem levantar a população dela (e sem chamar outra função). Cada conflito traz a regra, a prioridade, o valor e quantas pessoas em comum.

### D2. Simulação

`simular` chama a função (o laço de `resolver_regra` continua no endpoint). A resposta ganha `conflitos`, `departamentos` (quantos departamentos distintos entre os afetados) e, em cada pessoa, `cargo_id`, `departamento_id` e `valor_matriz` (o parâmetro na matriz do contrato, por `|get:`), para a tela mostrar "30 dias (matriz do contrato)" quando nenhuma regra se aplica. Simular continua sem alterar nada além da auditoria.

### D3. Conflito bloqueia

`enviar_aprovacao` e `aprovar` chamam a função e recusam com "Conflito não resolvido com …" quando há conflito. `regras_override` GET chama a função só para as regras em `rascunho` ou `pendente_aprovacao` e devolve `conflitos` em cada uma (as vigentes não precisam).

### D4. Rejeitar, prioridade e justificativa

- `regras_override/{id}/rejeitar` POST: RH ou Admin, regra `pendente_aprovacao`, motivo de 5 a 1000 caracteres; ninguém rejeita a própria regra (como na aprovação); vai a `rejeitada`; audita com o motivo.
- `regras_override/{id}/prioridade` PATCH: RH ou Admin, regra em `rascunho` ou `pendente_aprovacao`, prioridade de 1 a 99; audita antes e depois. É o "Definir prioridade" da simulação.
- `aprovar` aceita `justificativa` opcional, gravada na auditoria.

### D5. Tela

- Uma página ("Regras", menu de RH e Admin) com duas vistas: a lista (287:884) e a simulação (288:886), aberta por "Simular" ou depois de criar uma regra, com "← Voltar para Regras".
- Lista: filtros Todos, Pendentes de aprovação, Com conflito e Vigentes; trilha de instrumentos e de regras, com selo e ações por situação:
  - instrumento em rascunho: Enviar para aprovação; pendente: Rejeitar e Aprovar (desligado para quem criou, com "Você criou este instrumento: outra pessoa precisa aprovar"; e, nos coletivos sem registro no MTE, "Sem registro no MTE: não dá para aprovar ainda"); vigente ou outro: Ver detalhes;
  - regra em rascunho: Simular e Enviar para aprovação; pendente: Simular, Rejeitar e Aprovar (com conflito, o modal "conflito bloqueia" de 288:1391); vigente: Nova versão (abre "Nova regra" já preenchida) e Histórico (as versões do mesmo parâmetro, abrangência e escopo).
- "Nova regra de override" (288:1234) grava o rascunho e abre a simulação; dali sai "Enviar para aprovação".
- "Aprovar" (288:1293, 288:1321) usa o texto do "Aplicar regra" (288:1367) sobre vigência, versão e histórico, porque aprovar já publica.
- Nomes de departamento, cargo e pessoa vêm do `organograma`; o título do instrumento, da lista de instrumentos.

## Risks / Trade-offs

- [`impacto_override` roda a cada regra pendente na lista] → só rascunhos e pendentes, que são poucos; a população é uma consulta por regra.
- [`resolver_regra` filtra `data_fim` com `||` no `where`, que neste workspace não filtrava direito] → fora do escopo; registrado em `docs/figma-pendencias.md` e na regra de negócio para uma correção própria.
- [Erro de execução do XanoScript] → `tools/testar_regras_http.py` com login de verdade (cria rascunhos de teste e os rejeita ao fim).

## Migration Plan

1) Função nova (`CREATE`); 2) endpoints novos (`CREATE`) e alterados (`UPDATE`, conferidos contra o que está no ar). Rollback: publicar de novo as versões do git.
