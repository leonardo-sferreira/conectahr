# Design

## Context

Ver proposal.md. Pontos do código levantados em 23/10/2026:
- **Tabelas de pedido:** `solicitacao_rh` (tipos `alteracao_cadastral`, `declaracao`, `documento_avulso`, `outra` e `privacidade_lgpd`, este com `prazo_resposta`), `solicitacao_desligamento`, `ferias`, `ausencia`, `correcao_ponto` e `solicitacao_acesso`. A `delegacao_aprovacao` não é um pedido: é criada direto, sem decisão.
- **Feriados:** a tabela `feriado` (data, nome, estado, município, ativo) já existe, mantida pelo RH em "Estrutura da empresa"; os nacionais vêm da BrasilAPI.
- **Datas no XanoScript:** não há subtração de datas no XanoScript usado no projeto; somar com `add_secs_to_timestamp` funciona (change `treinamento-em-video`).
- **Sem Background Tasks:** o que depende de data roda na rotina diária manual (`rotinas/processar_diarias`).

## Decisions

### D1. Tipo → setor responsável → SLA padrão

| Tipo de solicitação | Tabela | Setor responsável | SLA padrão |
|---|---|---|---|
| Alteração cadastral | `solicitacao_rh` (`alteracao_cadastral`) | `rh` | 72 h úteis |
| Declaração | `solicitacao_rh` (`declaracao`) | `rh` | 72 h úteis |
| Documento avulso | `solicitacao_rh` (`documento_avulso`) | `rh` | 72 h úteis |
| Outra | `solicitacao_rh` (`outra`) | `rh` | 72 h úteis |
| Privacidade (LGPD) | `solicitacao_rh` (`privacidade_lgpd`) | `rh` | 72 h úteis, sem passar do prazo legal (D3) |
| Desligamento | `solicitacao_desligamento` | `rh` | 72 h úteis (o exemplo do pedido sugere 24 h; fica a critério do Admin) |
| Férias | `ferias` | `gestor` (o superior direto decide) | 72 h úteis |
| Ausência | `ausencia` | `rh` (o superior acompanha) | 72 h úteis |
| Correção de ponto | `correcao_ponto` | `gestor` | 72 h úteis |
| Pedido de acesso | `solicitacao_acesso` | `admin` | 72 h úteis |
| Delegação | `delegacao_aprovacao` | — | **Fora**: é criada direto, sem decisão |

**`sla_config`:**
- **Campos:**
  - `setor` (`rh`, `gestor`, `admin`) e `tipo_solicitacao` (enum com os 10 tipos acima);
  - `horas_uteis` (de 1 a 720), `ativo`, `atualizado_por_user_id` e `updated_at`;
  - o par (`setor`, `tipo_solicitacao`) é único.
- **Sem linha ativa, vale o padrão de 72 horas úteis.**

### D2. Horas úteis

- **Decisão:**
  - o relógio corre só em dias úteis: segunda a sexta, menos os feriados nacionais ativos da tabela `feriado`, os sem estado e sem município;
  - o dia útil vale 24 horas, no fuso America/Sao_Paulo;
  - 72 horas úteis = 3 dias úteis; 24 horas = 1 dia útil.
- **A lista de feriados é a tabela `feriado`:** ela já existe e o RH a mantém. Não entra um parâmetro novo.
- **Alternativa registrada, não adotada:** contar só o expediente das 9h às 18h. Assim, 72 horas viram 8 dias úteis. Ficaria mais longo e difícil de explicar.
- **Cálculo** (`ConectaHR/somar_horas_uteis(inicio, horas)`):
  1. se o início cai em dia não útil, ele passa para 00:00 do próximo dia útil;
  2. soma `floor(horas / 24)` dias úteis, de 24 em 24 horas com `add_secs_to_timestamp`, pulando os dias não úteis;
  3. soma o resto (`horas mod 24`) em horas; se o resultado cair em dia não útil, anda de 24 em 24 horas até um dia útil, mantendo o horário.
  - O dia da semana sai de `format_timestamp:"N":"America/Sao_Paulo"`. Os feriados entram como texto ",2026-11-02,2026-11-15," para o `contains`.
  - No máximo 720 horas, ou seja, 30 dias úteis no laço.
- **Conferência:**
  - aberta segunda às 10h, 72 horas → quinta às 10h;
  - aberta sexta às 10h → quarta às 10h;
  - aberta sábado às 15h → quarta às 00h (o relógio começa segunda às 00h);
  - com feriado na terça, a segunda às 10h vai para sexta às 10h.

### D3. Prazo gravado na abertura

- **No POST de cada tipo, `ConectaHR/prazo_sla(setor, tipo, aberta_em)` grava:**
  - `sla_horas`: o SLA vigente na hora;
  - `prazo_sla`: o início mais as horas úteis;
  - `alerta_sla`: o início mais 80% das horas úteis, arredondado para baixo, no mínimo 1 hora.
- **Decisão:** mudar o SLA depois não altera as solicitações já abertas, que guardam o prazo e as horas da abertura.
- **Pedido LGPD:** `prazo_sla` = o menor entre o calculado e o `prazo_resposta` legal (15 dias). O Admin não grava mais de 240 horas úteis para `privacidade_lgpd`.
- **Pedidos abertos antes da change ficam sem prazo**, e a tela mostra "Sem prazo".

### D4. Configuração

- **`sla_config` GET** (Admin, RH e Gestor): a lista dos 10 tipos com o SLA vigente, o padrão quando não há linha, quem alterou e quando.
- **`sla_config` POST e `sla_config/{id}` PATCH:**
  - só o Admin; horas de 1 a 720;
  - auditados com o valor anterior e o novo (`alterar_sla`).
  - RH e Gestor recebem 403.

### D5. Situação (na leitura)

- **Com o pedido em aberto:**
  - "vencido", se `now > prazo_sla`;
  - "perto de vencer", se `now >= alerta_sla`;
  - "no prazo", nos demais casos.
- **Com o pedido decidido:** "atendido no prazo" ou "atendido fora do prazo", comparando a data da decisão com `prazo_sla`.
- **`central_de_tarefas`** devolve `prazo_sla` e a situação, ordenada pelo prazo mais próximo; os vencidos vêm primeiro.
- **Decisão:** "perto de vencer" é a partir de 80% do tempo útil (`alerta_sla` gravado na abertura), porque o XanoScript do projeto não subtrai datas para calcular a proporção na leitura.

### D6. Telas

- **Para quem decide e para quem pediu:** um selo "Responder até {dd/mm hh:mm}" com o tom da situação (verde, âmbar ou vermelho; cinza para "Sem prazo").
- **Configurações → "SLA de solicitações":**
  - uma tabela por setor e tipo, com o SLA e "padrão" quando não há linha;
  - o Admin edita as horas num modal;
  - o RH vê só a leitura; o Gestor não tem a aba e vê o prazo nas filas.

### D7. Aviso de "perto de vencer"

- **Na rotina diária:** para cada pedido em aberto com `now >= alerta_sla` e sem `aviso_sla_em`, avisa quem decide (pela mesma regra do `notificar_decisores`, tipo novo `prazo_vencendo`) e grava `aviso_sla_em`. É idempotente.
- **Depende da change `notificacoes-de-publicacao`** (o enum e a preferência). Se ela não estiver pronta, esta parte espera.

## Risks

- **O laço dia a dia no XanoScript** custa até 30 voltas por pedido. É aceitável no POST; nas listas, a situação só compara timestamps já gravados.
- **Feriado cadastrado depois da abertura** não muda os prazos já gravados (coerente com o D3).
- **Rotina diária manual:** sem ela, o aviso atrasa. O selo na fila continua certo, porque é calculado na leitura.
