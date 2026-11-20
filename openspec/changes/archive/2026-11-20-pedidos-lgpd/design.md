# Design

## Context

Ver proposal.md. O pedido do titular nasce em `solicitacoes` POST (tipo `privacidade_lgpd`, um de sete subtipos, `prazo_resposta` = abertura + 15 dias, LGPD art. 19, II). `atender` e `indeferir` já existem, com o bloqueio de autoaprovação (auditado), a auditoria da decisão e o aviso ao titular (sino e e-mail, pela preferência "Solicitações").

## Decisions

### D1. Resultado e resposta

- `solicitacao_rh.resultado_lgpd` (opcional): `atendido`, `atendido_parcial` ou `nao_atendido`. Só os pedidos LGPD recebem o valor.
- `solicitacoes/{id}/atender`:
  - aceita `resultado` (`total` ou `parcial`; vazio = `total`); `parcial` grava `atendido_parcial`, e o status fica `atendida`, porque o pedido está respondido;
  - no pedido LGPD, exige `justificativa_decisao` (a resposta ao titular) com 5 caracteres ou mais. Nos outros tipos, nada muda.
- `solicitacoes/{id}/indeferir`: no pedido LGPD, grava `nao_atendido` (a justificativa já era obrigatória).
- Não muda o enum de status, para não afetar "Solicitações ao RH", a Central e os avisos.

### D2. Tela "Pedidos LGPD" (RH; Figma 249:5709 e 249:5955)

- **Dados:** `solicitacoes` GET (filtrado na tela pelo tipo `privacidade_lgpd`) e `organograma` (nome e departamento).
- **Indicadores:** abertos, vencendo em 3 dias (abertos com prazo em até 3 dias ou vencido) e respondidos no ano.
- **Abas:** "Abertos" (recebida e em análise), ordenada pelo prazo, e "Respondidos" (atendida e indeferida), dos mais recentes para os mais antigos. Filtro de tipo pelos sete subtipos.
- **Tabela:**
  - pessoa e departamento, pedido (tipo e começo do texto), aberto em e prazo;
  - o prazo vem em vermelho quando falta 3 dias ou menos, em âmbar quando está no prazo, e "venceu dd/mm" quando já passou;
  - a linha que está vencendo fica destacada.
- **"Responder →":** abre o modal com pessoa, pedido, prazo, o texto do titular, a decisão (três opções) e a resposta. "Não atendido" chama `indeferir`; as outras chamam `atender`. Fica desligado no próprio pedido. A recusa do backend aparece no modal.
- **"Ver",** nos respondidos: a decisão e a resposta enviada.
- **Rodapé do Figma:** "Todo pedido e resposta ficam na auditoria. O encarregado (DPO) acompanha esta fila."
- **Abertura:** a API não devolve `created_at` (privado), então "Aberto em" usa o prazo menos 15 dias.

### D3. Titular

Em "Meus pedidos de privacidade", o selo mostra "Atendido em parte" quando for o caso, e o detalhe traz "Resposta do RH: ...".

## Risks / Trade-offs

- [Resposta de pedido LGPD já atendido sem texto] → os antigos continuam como estão; a regra vale a partir de agora.
- [Erro de execução do XanoScript] → conferir com um pedido de teste respondido pela tela (as três decisões).

## Migration Plan

1. Tabela: `ADD_FIELD` de `resultado_lgpd`.
2. Endpoints: `UPDATE` de `atender` e `indeferir`, conferidos contra o que está no ar.

Rollback: publicar as versões do git.
