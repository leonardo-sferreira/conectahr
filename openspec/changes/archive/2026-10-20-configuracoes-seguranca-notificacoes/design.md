# Design

## Context

Ver proposal.md. Avisos do sino nascem de três jeitos: pela função `ConectaHR/notificar` (23 chamadas), pela `ConectaHR/notificar_decisores` (pedidos novos para quem decide) e por `db.add notificacao_interna` direto em alguns endpoints. E-mails vão para `email_outbox`; o envio é manual (RH ou Admin processam a fila).

## Decisions

### D1. Segurança

- Trocar senha usa `auth/senha` (PATCH), que já confere a senha atual, a confirmação, o tamanho (8 a 64) e que a nova é diferente. A tela mostra as três regras do Figma ("8 caracteres ou mais", "Letras e números", "Diferente da senha atual") ficando verdes conforme a pessoa digita. Letras e números é conferido na tela; o backend fica como está.
- Ao trocar a senha, o backend encerra as **outras** sessões ativas (a do token continua) e audita `encerrar_outras_sessoes` com a quantidade, como `auth/sessoes/encerrar_outras` já faz. Vale também no primeiro acesso.
- Sessões e dispositivos: só as ativas, das mais recentes, com o navegador gravado no login ("Chrome no Windows"), o IP e "ativo agora" (a atual) ou a data de início. A atual vem marcada por `sessao_atual_id` e não tem "Encerrar". Encerrar a sessão atual não é oferecido: para isso existe "Sair".

### D2. Assuntos e canais

Tabela `preferencia_aviso` (`user_id`, `assunto`, `plataforma`, `email`), um registro por pessoa e assunto; sem registro, tudo ligado.

| Assunto | Origem (recurso) | E-mail existente |
|---|---|---|
| `ferias_ausencias` | `ferias`, `ausencia` | Férias aprovadas |
| `ponto` | `correcao_ponto`, `registro_ponto` | — |
| `documentos` | `documento`, `pendencia_documento` | Documento vencendo |
| `avaliacoes_metas` | `avaliacao`, `formulario_meta` | Avaliação disponível |
| `solicitacoes` | `solicitacao_rh` | Solicitação atendida ou indeferida |

Sempre ligados (não aparecem no PATCH): benefícios, alertas de segurança (login, e-mail da conta alterado), cadastro atualizado, acesso e desligamento, e **todo `pedido_novo`**, que é trabalho esperando a decisão da pessoa. "Solicitações ao RH" entra mesmo sem estar no Figma, porque já manda e-mail e sem a linha não daria para desligá-lo.

### D3. Onde a preferência vale

- `notificar`: calcula o assunto pelo recurso (exceto `pedido_novo`) e não cria o aviso se a pessoa desligou "Na plataforma". `notificar_decisores` não muda (só pedidos novos).
- Avisos gravados direto: `avaliacoes_POST`, `solicitacoes/{id}/atender` e `indeferir`, `ferias/{id}/aprovar`, `documentos/processar_vencimentos` e `folha_ponto/tratar` consultam a preferência do destinatário antes de gravar o aviso e, onde há, antes de pôr o e-mail na fila. A consulta a `preferencia_notificacao` sai desses endpoints.
- `gerar_pendencias_obrigatorias` (documentos pedidos na admissão) continua sempre ligado: é o começo do vínculo.
- `ponto/marcar` não muda: é o endpoint do REP-P, e o aviso dele (descanso interjornada) é um alerta legal, sempre entregue.

## Risks / Trade-offs

- [`notificar` é chamada por 23 endpoints; um erro nela derruba todos] → mudança mínima (uma consulta e uma condição, no padrão já usado); `tools/testar_configuracoes_http.py` com login de verdade e um fluxo que gera aviso, depois do push.
- [Preferências antigas deixam de valer] → quem tinha desligado algum e-mail volta a recebê-lo até escolher de novo; nenhuma conta de produção alterou isso até hoje (a tela nunca existiu).
- [Encerrar as outras sessões na troca de senha pega a pessoa de surpresa em outro aparelho] → o Figma já avisa no texto do cartão.

## Migration Plan

Pushes separados: 1) tabela `preferencia_aviso` (só `CREATE`); 2) endpoints novos (`CREATE`) e alterados (`UPDATE`, conferidos um a um no dry-run); 3) a função `notificar`. Rollback: publicar de novo as versões anteriores do git.
