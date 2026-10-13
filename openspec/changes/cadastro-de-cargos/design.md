# Design

## Contexto

`cargo` tem `nome` (único), `descricao`, `salario_base`, `ativo` e, desde a change `organograma-hierarquia`, `nivel_hierarquico_id`. `cargos` POST e `cargos/{id}` PATCH existem (RH e Admin), sem tela. A admissão escolhe o cargo numa lista única. A pessoa tem um L1–L5 (`colaborador.nivel`) que alimenta o Plano de carreira e o histórico profissional.

## Decisões

### D1. Senioridade no cargo (decisão do usuário, 13/10/2026)
Cada combinação é um cargo: "Desenvolvedor Front-end Pleno" é um registro, com salário base próprio. É o título da carteira de trabalho; promoção vira troca de cargo, que o histórico profissional já guarda. `cargo.senioridade` é um enum (`junior`, `pleno`, `senior`, `especialista`) opcional, só para filtrar e rotular.

### D2. O nome guarda o título completo
O índice único de `cargo.nome` continua. A tela pede o nome-base ("Desenvolvedor Front-end") e a senioridade e monta o título ("Desenvolvedor Front-end Pleno"), que é o que vai para o backend. Na edição, a tela tira a senioridade do fim do nome para mostrar o nome-base. Assim não é preciso trocar o índice único da tabela.

### D3. Departamento no cargo (decisão do usuário)
`cargo.departamento_id` opcional. Cargo sem departamento serve a qualquer departamento (ex.: "Estagiário"). Na admissão, a lista de cargos segue o departamento escolhido.

### D4. Endpoints
`cargos` POST e `cargos/{id}` PATCH ganham `senioridade` e `departamento_id` (e o POST, `nivel_hierarquico_id`), com a auditoria que já têm. O nível continua também em `cargos/{id}/nivel` PATCH. `organograma` GET passa a devolver `departamento_id` e `senioridade` de cada cargo; o salário continua só em `listar_cargos` (RH e Admin).

### D5. Duas etapas (decisão do usuário)
Esta change não mexe no L1–L5 da pessoa. A troca do L1–L5 pelo nível do cargo, com o Plano de carreira por cargo, fica numa change própria.
