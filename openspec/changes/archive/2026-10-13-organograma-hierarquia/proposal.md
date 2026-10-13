# Proposal

## Why

O organograma de hoje é um quadro fixo por departamento (gestor do departamento e a equipe), e o "Ver organograma completo" do Perfil ainda não abre nada. O usuário pediu (13/10/2026) um organograma **público e navegável**: clicar no topo (ex.: CEO) e descer pelos níveis, ver o superior de cada pessoa, quem é de cada setor e onde cada um está, com o nível do cargo à vista. Cada empresa tem a sua hierarquia (CEO, diretoria, heads, gerência, coordenação, supervisão, analistas, operadores, estagiários...), então os níveis não podem ser fixos no código.

## What Changes

- **Níveis hierárquicos da empresa:** nova tabela `nivel_hierarquico` (nome e ordem, do topo para a base), mantida pelo RH e pelo Admin, com inclusão, edição e desativação auditadas.
- **Cargo com nível:** `cargo.nivel_hierarquico_id` (opcional). O RH define o nível de cada cargo por um endpoint próprio, sem mexer no salário base.
- **Organograma pelo superior direto:** a árvore segue `colaborador.superior_colaborador_id` (o vínculo que o RH já define em Colaboradores). Quem não tem superior fica no topo. O nível do cargo ordena e rotula as pessoas.
- **`organograma` GET** passa a devolver o superior direto de cada pessoa, o nível de cada cargo e a lista de níveis. Continua público para qualquer perfil logado e só com nome, cargo, nível e departamento (nada de e-mail, CPF ou salário).
- **Tela "Organograma"** navegável: começa na própria pessoa com o caminho até o topo; clicar numa pessoa mostra o superior dela e quem está abaixo; busca por nome ou cargo, filtro por departamento e "Minha posição". O Perfil passa a abrir a tela.
- **Estrutura da empresa:** abas "Níveis" (cadastro e ordem) e "Cargos" (nível de cada cargo), para RH e Admin.

## Non-goals

- Nível de carreira por pessoa (L1, L2...): o "level" é o nível do cargo (decisão do usuário).
- Editar o superior direto pela tela do organograma: continua em Colaboradores → "Definir superior".
- Mostrar e-mail: o cadastro só tem o e-mail pessoal, que não vai para uma tela pública (LGPD).
- Desenho automático em árvore com linhas (o Streamlit não tem componente nativo): a navegação é por níveis, um passo de cada vez.

## Impact

- Backend: `table/nivel_hierarquico.xs` (nova), `table/cargo.xs`, `api/conecta_rh_cargos/` (níveis e nível do cargo), `api/conecta_rh_departamentos/organograma_GET.xs`.
- Frontend: `pagina_organograma.py` e `organograma_modelo.py` (novos), `pagina_estrutura.py`, `pagina_perfil.py`, `app.py`, `api_client.py`.
- Figma: tela Organograma (224:3593) navegável e as abas Níveis e Cargos da Estrutura da empresa.
