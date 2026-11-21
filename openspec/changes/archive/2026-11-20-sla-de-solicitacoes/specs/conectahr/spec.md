## ADDED Requirements

### Requirement: SLA de atendimento em horas úteis
Cada tipo de solicitação SHALL ter um SLA de atendimento em horas úteis, configurado por setor responsável e tipo, com o padrão de 72 horas úteis quando não há configuração. As horas úteis SHALL contar só os dias úteis (segunda a sexta, sem os feriados nacionais), com o dia útil valendo 24 horas, no fuso de São Paulo. Cada solicitação SHALL gravar o prazo na abertura, e mudar o SLA depois SHALL NOT alterar as solicitações já abertas. O pedido LGPD SHALL NOT ter prazo maior que o prazo legal.

#### Scenario: Aberta na segunda
- **WHEN** uma solicitação sem SLA configurado é aberta numa segunda-feira às 10h
- **THEN** o prazo é a quinta-feira às 10h

#### Scenario: Aberta na sexta
- **WHEN** uma solicitação sem SLA configurado é aberta numa sexta-feira às 10h
- **THEN** o prazo é a quarta-feira seguinte às 10h, sem contar o fim de semana

#### Scenario: SLA alterado
- **WHEN** o Admin muda o SLA de Desligamento para 24 horas úteis
- **THEN** o novo pedido de desligamento recebe o prazo de 1 dia útil, e os já abertos mantêm o prazo anterior

### Requirement: Só o Admin altera o SLA
O backend SHALL permitir criar e alterar o SLA só ao Admin, com auditoria do valor anterior e do novo. RH e Gestor SHALL poder só ler.

#### Scenario: RH tenta alterar
- **WHEN** o RH ou o Gestor tenta alterar um SLA
- **THEN** o backend recusa com 403

### Requirement: Situação do prazo nas filas
As filas de quem decide e a tela de quem pediu SHALL mostrar "Responder até {data/hora}" com a situação no prazo, perto de vencer (a partir de 80% do tempo útil) ou vencido. A central de tarefas SHALL ordenar pelo prazo mais próximo, com os vencidos primeiro. Quem decide SHALL receber um aviso quando o pedido fica perto de vencer.

#### Scenario: Pedido vencido
- **WHEN** um pedido passa do prazo sem decisão
- **THEN** ele aparece como "vencido" na fila e no topo da central de tarefas
