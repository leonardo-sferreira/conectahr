# Design

## Context

Ver proposal.md. Pontos do código levantados em 23/10/2026:
- **`ConectaHR/notificar`:** cria um aviso para uma pessoa (pelo usuário ou pelo colaborador). Não avisa o autor da ação e respeita a preferência "Na plataforma" do assunto.
- **`ConectaHR/notificar_decisores`:** escolhe quem decide com o parâmetro `quem`, que pode ser `superior`, `rh` ou `superior_e_rh`.
- **`preferencia_aviso.assunto`:** hoje são `ferias_ausencias`, `ponto`, `documentos`, `avaliacoes_metas` e `solicitacoes`. Sem registro, os dois canais estão ligados.
- **Limites do plano:** sem Background Tasks e com 10 requisições a cada 20 segundos.

## Decisions

### D1. Função `ConectaHR/notificar_publico`

- **Entrada:**
  - `publico` (`todos` ou `departamentos`) e `departamento_ids` (texto ",1,4,", o padrão do projeto);
  - `autor_user_id`, `tipo`, `assunto`, `titulo`, `mensagem`, `recurso` e `registro_id`.
- **Uma só consulta busca os destinatários:** colaboradores não desligados com conta ativa, filtrados pelo departamento quando o público é por setor. Fica de fora quem desligou o assunto em "Na plataforma" e o autor da ação.
- **Grava um `db.add` por pessoa, dentro da mesma chamada.** Uma publicação é uma requisição só, mesmo com muitos destinatários. **Na implementação (23/10/2026):** o `db.bulk.add` da documentação do XanoScript é recusado pelo push desta instância ("Syntax error"), então ficou o laço.
- **Devolve** quantos avisos criou. Ela não escreve na auditoria: quem audita é a ação que publicou.
- **Decisão:** a função nova não chama `ConectaHR/notificar` pessoa a pessoa, para não fazer N consultas de preferência. Ela repete a mesma regra (preferência e autor) numa consulta só.

### D2. Treinamento novo

- **Dispara:**
  - em `treinamentos` POST, com `ativo` verdadeiro (sempre, na criação);
  - em `treinamentos/{id}` PATCH, quando `ativo` passa de falso para verdadeiro.
- **Público:** o do treinamento (`publico` e `departamento_ids`). Treinamento opcional também avisa: é um convite, não uma cobrança.
- **Aviso:** tipo `treinamento_novo`, assunto `treinamentos`. Título "Novo treinamento disponível: {nome}"; mensagem com a validade e "Veja em Meus treinamentos". `recurso = "treinamento"`.
- **Editar um treinamento já ativo não avisa de novo.**

### D3. Pesquisa nova

A pesquisa de clima só fica respondível com perguntas e dentro do período (`ativo`, `data_inicio <= hoje <= data_fim`). As perguntas entram depois da criação, em `pesquisas_clima/{id}/perguntas`, e **só antes de a pesquisa abrir** (a rota recusa depois). Por isso o convite não sai nem na criação nem nas perguntas: sai no dia em que a pesquisa abre.

- **Disparo:** sai uma vez, quando a pesquisa fica respondível. O campo `pesquisa_clima.convite_enviado_em` evita repetir, e é gravado **antes** de avisar: uma segunda leitura ao mesmo tempo já não acha a pesquisa pendente.
- **Decisão (na implementação):** como o plano não tem tarefa agendada e a rotina diária é manual, o convite também sai na leitura, no primeiro acesso ao Início do dia. A rotina continua mostrando o que falta enviar em `status_operacional`. Pontos cobertos:

| Tipo | Ponto de disparo | Observação |
|---|---|---|
| Pesquisa de clima (`tipo = clima`) | A função `ConectaHR/enviar_convites_pesquisa`, chamada no primeiro acesso ao Início do dia (`humor` GET, que todo mundo chama) e na rotina diária | Público: todos os ativos (a pesquisa não tem público por setor) |
| Avaliação psicossocial NR-1 (`tipo = psicossocial`) | O mesmo da pesquisa de clima (é a mesma tabela) | Change `riscos-psicossociais` |
| Termômetro de humor | A mesma função, no primeiro acesso ao Início de cada ciclo de 10 dias e na rotina diária (um convite por ciclo, marcado em `humor_convite`, com chave única) | Change `termometro-de-humor`; o cartão no Início continua sendo o lembrete principal |
| Avaliação 360 / de desempenho | Já avisa: `ciclos_avaliacao/{id}/atribuir` e `avaliacoes` POST (`avaliacao_disponivel`) | Sem mudança; só conferir no teste |

- **Aviso:** tipo `pesquisa_nova`, assunto `pesquisas`. Título "Nova pesquisa: {título}"; mensagem com o período e "É anônima".
- **Anonimato:**
  - o convite é igual para todos e não guarda nada sobre a resposta;
  - marcar como lido não cria participação;
  - responder não marca o aviso como lido;
  - nenhuma consulta cruza `notificacao_interna` com as tabelas de participação.

### D4. Solicitação para decidir: evento → quem recebe

| Evento | Rota | Quem recebe (`pedido_novo`) | Situação |
|---|---|---|---|
| Solicitação ao RH | `solicitacoes` POST | RH (`quem = rh`) | Já avisa |
| Pedido de desligamento | `solicitacoes_desligamento` POST | RH (`quem = rh`) | Já avisa |
| Férias | `ferias/solicitacoes` POST | Superior direto; sem ele, o gestor do departamento; sem nenhum, o RH | Já avisa |
| Ausência | `ausencias` POST | Superior e RH | Já avisa |
| Correção de ponto | `ponto/correcao` POST | Superior | Já avisa |
| Documento enviado para conferência | `documentos` POST | RH | Já avisa |
| Pedido de acesso (troca de perfil) | `solicitacoes_acesso` POST | Admins ativos | Já avisa (`ConectaHR/notificar` direto) |
| Delegação criada | `delegacoes` POST | **O substituto** | **Lacuna:** criar o aviso (tipo `pedido_novo`, recurso `delegacao`, "Você recebeu a delegação de {titular} de {início} a {fim}") |
| Pedido durante uma delegação ativa | `ConectaHR/notificar_decisores` | O decisor **e o substituto** com delegação ativa no escopo | **Lacuna:** incluir o substituto na função |
| Reatribuir ou encaminhar uma solicitação a outra pessoa | — | — | **Não existe** esse fluxo hoje. Se for criado, deve usar `notificar` para o novo responsável |

### D5. Lembretes (opcional)

Entram na rotina diária (`ConectaHR/processar_transicoes_diarias`), que já é idempotente:
- `treinamento_vencendo`: obrigatório que vence em 30 dias, um aviso por conclusão;
- `pesquisa_encerrando`: pesquisa que fecha amanhã, para quem ainda não respondeu.

**O lembrete da pesquisa iria só para quem não respondeu**, e isso usa a participação. Para não ligar a pessoa à resposta, ele vai para todo o público, com o texto "Se ainda não respondeu…".

**Decisão:** o D5 fica para o fim. Se o prazo apertar, sai desta change.

### D6. Preferências

- Os assuntos `treinamentos` e `pesquisas` entram em `preferencia_aviso` e na tela Configurações → Notificações, com "Na plataforma". A coluna de e-mail mostra "Sem e-mail", como no ponto, porque não há modelo de e-mail para eles.
- **O assunto `treinamentos` também vale para o aviso "Treinamento registrado"** (a conclusão registrada pelo RH, recurso `treinamento`), porque `ConectaHR/notificar` escolhe o assunto pelo recurso.
- Sem registro, a plataforma fica ligada, como nos demais assuntos.

## Risks

- **Público "todos" numa empresa grande:** muitas linhas por publicação. Mitigação: o lote, uma requisição só; a retenção de F16 (2 anos) já limpa as antigas.
- **A rotina diária é manual:** se ninguém a rodar, o convite da pesquisa com início futuro atrasa. Mitigação: o disparo também ocorre no `perguntas` POST quando a pesquisa já está no período, e a Central mostra a rotina pendente.
