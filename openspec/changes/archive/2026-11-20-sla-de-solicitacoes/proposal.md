# Proposal

## Why

Mapeamento de Leonardo (23/10/2026). Hoje as solicitações não têm prazo de atendimento, salvo o pedido LGPD (15 dias, art. 19). Quem pediu não sabe até quando espera a resposta. Quem decide não vê o que está atrasando, e a empresa não mede o atendimento.

## What Changes

- **Prazo (SLA) por setor e tipo de solicitação**, em horas úteis. O padrão é 72 horas úteis, e **só o Admin altera** (D1, D4).
- **Horas úteis** (D2): só dias úteis contam (segunda a sexta, sem os feriados nacionais da tabela `feriado`), com o dia útil valendo 24 horas. 72 horas úteis = 3 dias úteis.
- **Prazo gravado na abertura** (D3): cada solicitação grava `prazo_sla` com o SLA vigente. Mudar o SLA depois não muda as já abertas.
- **Situação calculada na leitura** (D5): no prazo, perto de vencer (20% ou menos do prazo) ou vencido. A central de tarefas ordena pelo prazo mais próximo.
- **Telas** (D6):
  - "Responder até {data/hora}" com a situação, para quem decide e para quem pediu;
  - a aba nova "SLA de solicitações" em Configurações (Admin edita; RH só lê).
- **Aviso de "perto de vencer"** para quem decide, na rotina diária (D7), integrado à change `notificacoes-de-publicacao`.

## Non-goals

- Contar só o horário de expediente (9h às 18h): a alternativa fica registrada no D2, mas não entra.
- Feriados estaduais e municipais: só os nacionais.
- Pausar o relógio enquanto se espera a pessoa (por exemplo, um documento pendente).
- Mudar o prazo legal do pedido LGPD.
- Delegações: não são pedidos com decisão (D1).

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: SLA de atendimento por setor e tipo de solicitação, com prazo gravado na abertura e situação nas filas.

## Impact

- **Backend:**
  - tabela nova `sla_config`;
  - campos `prazo_sla`, `alerta_sla` e `sla_horas` em `solicitacao_rh`, `solicitacao_desligamento`, `ferias`, `ausencia`, `correcao_ponto` e `solicitacao_acesso`;
  - funções novas `ConectaHR/somar_horas_uteis` e `ConectaHR/prazo_sla`;
  - endpoints novos `sla_config` GET e POST e `sla_config/{id}` PATCH;
  - alterados: o POST de cada tipo (grava o prazo), as listagens e a `central_de_tarefas` (prazo e ordem), e `ConectaHR/processar_transicoes_diarias` (o aviso).
- **Frontend:**
  - `api_client.py` e um modelo novo `sla_modelo.py`;
  - as filas: Central de Pendências, Solicitações ao RH, Desligamentos, Férias, Ausências, Folha de ponto e Usuários e perfis;
  - "Meus pedidos" de cada tela;
  - `pagina_configuracoes.py` (a aba nova).
- **Figma:** a aba "SLA de solicitações" (Admin, e a leitura para o RH), o selo de prazo nas filas e em "Meus pedidos", nos temas claro e escuro.
- **Testes:**
  - novos `tools/testar_sla.py` e `tools/testar_sla_http.py`;
  - os testes de cada fila conferem o selo.
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção nova);
  - `docs/indicadores.md` (atendimento no prazo, opcional).
