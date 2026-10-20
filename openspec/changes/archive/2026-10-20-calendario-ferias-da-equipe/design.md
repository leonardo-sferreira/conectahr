# Design

## D1. Escopo e dados devolvidos

O escopo é o mesmo de `folha_ponto/pessoas` (tarefa 81): RH e Admin veem todos; os demais veem a si mesmos, quem os tem como superior direto e, de quem não tem superior, o departamento que gerenciam. Desligados e anonimizados ficam de fora. Assim, quem decide o pedido (o superior direto ou o gestor do departamento, regra de `ferias/{id}/aprovar`) é quem vê.

Cada item traz só `nome`, `departamento_id`, `data_inicio`, `data_fim`, `quantidade_dias`, `status` e `e_voce`. Observação, abono e dados de decisão não saem (minimização, LGPD). Situações: `Aprovada`, `Concluida` e `Pendente`; `Rejeitada` e `Cancelada` não aparecem. O pedido em análise entra porque é o que o gestor está para decidir.

O filtro de período é por sobreposição (`data_inicio <= ate` e `data_fim >= desde`), e a tela pede o mês inteiro, guardado por 20 s para cada mês visto.

## D2. A tela

- A aba só aparece para Gestor, RH, Admin e quem tem equipe (`tem_equipe`, a mesma checagem do menu). RH sem cadastro de colaborador também vê a equipe.
- Cada dia mostra até três nomes curtos ("Ana R."), verdes para aprovadas e âmbar para em análise, e "+N" para o resto; feriados continuam marcados.
- "Alertar a partir de" (padrão 2, de 2 a 50): o dia que chega a esse número ganha borda vermelha, e um alerta diz em quantos dias do mês isso acontece e o pico ("Pico: 4 pessoas em 15/12").
- Indicadores: pessoas acompanhadas, quem tem férias no mês e o pico no mesmo dia. A lista do mês segue a data de início.
