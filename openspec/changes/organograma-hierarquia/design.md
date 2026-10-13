# Design

## Contexto

`organograma` GET devolve departamentos (com `gestor_colaborador_id`), cargos e colaboradores (`id`, `nome`, `cargo_id`, `departamento_id`). O Perfil monta um cartão com o gestor do departamento e os colegas. O vínculo pessoa a pessoa já existe: `colaborador.superior_colaborador_id`, definido pelo RH em Colaboradores e usado pelo ponto (quem decide correções). O cargo não tem nível.

## Decisões

### D1. Árvore pelo superior direto (decisão do usuário, 13/10/2026)
Abaixo de cada pessoa ficam as que a têm como `superior_colaborador_id`. Fica no topo quem não tem superior, quem aponta para alguém fora do organograma (desligado) ou quem faria um ciclo (A → B → A): o caminho até o topo para ao repetir alguém, e essa pessoa vira topo. O gestor do departamento não entra na árvore: ele continua valendo para as regras de decisão, mas o organograma mostra o vínculo direto.

### D2. Níveis por empresa, numa tabela
`nivel_hierarquico` (`nome` até 60, `ordem` inteiro, `ativo`) e `cargo.nivel_hierarquico_id` opcional. A ordem menor fica em cima. O usuário pediu que a hierarquia siga os cargos e níveis de cada empresa, então nada é fixo no código. O "level" que a pessoa acompanha é o nível do cargo (decisão do usuário).

### D3. Endpoints
No grupo `ConectaRH — Cargos`: `niveis_hierarquicos` GET (qualquer perfil logado), `niveis_hierarquicos` POST e `niveis_hierarquicos/{id}` PATCH (nome, ordem, ativo; RH e Admin, auditados) e `cargos/{id}/nivel` PATCH (só o nível, RH e Admin, auditado). O `cargos/{id}` PATCH existente exige nome, descrição e salário juntos; o endpoint próprio evita reenviar o salário para trocar o nível. `organograma` GET passa a devolver `superior_colaborador_id` de cada pessoa, `nivel_hierarquico_id` de cada cargo e os níveis ativos.

### D4. Tela navegável
O Streamlit não desenha árvore com linhas. A tela mostra uma pessoa em foco por vez: o caminho do topo até ela (clicável), o cartão dela com o superior acima e, abaixo, quem a tem como superior, em cartões clicáveis agrupados pelo nível. Começa na própria pessoa; "Topo" leva às pessoas sem superior; "Minha posição" volta. Busca (nome ou cargo) e filtro por departamento mostram uma lista de pessoas que leva ao foco. Diferença do Figma 224:3593 (árvore fixa por departamento), atualizada no Figma.

### D5. Dados na tela pública
Só nome, cargo, nível e departamento. A nota do Figma ("e-mail corporativo") sai: o cadastro só tem `email_pessoal`, que não vai para uma tela pública.

## Riscos

- Superior não definido: sem `superior_colaborador_id`, todos ficam no topo. A tela de Colaboradores já tem "Definir superior"; o RH precisa preencher.
- Ciclo de superiores: tratado na montagem (D1); o backend de "Definir superior" já recusa a pessoa como superior de si mesma.
