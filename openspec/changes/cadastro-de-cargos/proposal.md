# Proposal

## Why

O RH não tem onde cadastrar cargos pela tela: os cargos entram por endpoint, sem senioridade nem departamento. O usuário pediu (13/10/2026) que o RH cadastre os cargos da empresa como eles vão para a carteira de trabalho, com a senioridade (Júnior, Pleno, Sênior) e a área (ex.: "Analista de Contas a Pagar Pleno" no Financeiro, "Analista Contábil Júnior" na Contabilidade), para escolher nas próximas admissões. Pediu também que o level passe a ser o nível do cargo, em vez de uma faixa L1–L5 solta na ficha da pessoa.

## What Changes

Primeira etapa (decisão do usuário: em duas etapas):

- **Cargo com senioridade e departamento:** `cargo.senioridade` (Júnior, Pleno, Sênior ou Especialista; opcional) e `cargo.departamento_id` (opcional). O `nome` do cargo continua sendo o título completo, como vai na carteira ("Desenvolvedor Front-end Pleno"); a senioridade fica também separada, para filtrar e rotular.
- **Cadastro de cargos pelo RH:** na aba "Cargos" da Estrutura da empresa, "Novo cargo" e "Editar" com nome, senioridade, departamento, nível hierárquico, salário base e descrição; a tela mostra o nome que vai para a carteira antes de salvar. `cargos` POST e `cargos/{id}` PATCH passam a receber a senioridade e o departamento.
- **Admissão:** o cargo é escolhido entre os do departamento escolhido (e os sem departamento), com a senioridade e o nível à vista.
- **`organograma` GET** devolve o departamento e a senioridade de cada cargo (dados não sensíveis).

## Non-goals (segunda etapa, change própria)

- Tirar o L1–L5 (`colaborador.nivel`) da ficha, da admissão e do vínculo, e refazer o Plano de carreira (`plano_carreira` GET: próximo nível e competências) em cima de cargo e nível. Nesta etapa o L1–L5 continua como está.
- Senioridade por pessoa: a senioridade é do cargo (decisão do usuário); promoção de Júnior para Pleno é troca de cargo, que o histórico profissional já registra.

## Impact

- Backend: `table/cargo.xs`, `api/conecta_rh_cargos/cargos_POST.xs`, `cargos/id_PATCH.xs`, `api/conecta_rh_departamentos/organograma_GET.xs`.
- Frontend: `pagina_estrutura.py`, `organograma_modelo.py` (ou um modelo de cargos), `pagina_colaboradores.py`, `api_client.py`.
- Figma: aba Cargos da Estrutura da empresa (500:1156) com "Novo cargo" e o modal.
