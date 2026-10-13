# Tasks

## 1. Figma

- [x] 1.1 Redesenhar a tela Organograma (224:3593) navegável (caminho até o topo, pessoa em foco com o superior, quem está abaixo por nível, busca, departamento, "Minha posição") e as abas "Níveis" e "Cargos" da Estrutura da empresa (468:838). Verificar: prints dos nós.
  - **Feito (13/10/2026):** Organograma 224:3593 (caminho, superior, posição, abaixo por nível, "Minha posição"); Níveis 500:888 e Cargos 500:1156.

## 2. Backend

- [x] 2.1 Criar `table/nivel_hierarquico.xs` e `cargo.nivel_hierarquico_id` (schema publicado à parte). Verificar: dry-run só com ADD/UPDATE_FIELD.
- [x] 2.2 Criar `niveis_hierarquicos` GET/POST, `niveis_hierarquicos/{id}` PATCH e `cargos/{id}/nivel` PATCH (RH e Admin nas escritas, auditadas). Verificar: `tools/checar_endpoints.py` sem falha; por HTTP, Colaborador recebe 403 ao incluir nível (não verificado sem o código por e-mail).
  - **Feito (13/10/2026):** tabela e campo publicados à parte (CREATE e ADD_FIELD); 4 endpoints novos e `organograma` GET publicados; `checar_endpoints` 218 endpoints, 0 falhas. Teste por HTTP: não verificado (precisa do código de acesso por e-mail).
- [x] 2.3 `organograma` GET com `superior_colaborador_id`, `nivel_hierarquico_id` dos cargos e os níveis ativos. Verificar: `tools/checar_endpoints.py`.

## 3. Frontend

- [x] 3.1 `organograma_modelo.py`: árvore pelo superior (topo, filhos ordenados por nível e nome, caminho até o topo sem ciclo), busca e filtro. Verificar: `tools/testar_organograma.py`.
- [x] 3.2 `pagina_organograma.py`: foco, caminho, superior, quem está abaixo, busca, departamento, "Minha posição"; "Ver organograma completo" do Perfil abre a tela. Verificar: `tools/testar_organograma.py` com AppTest.
- [x] 3.3 Estrutura da empresa: abas "Níveis" (incluir, editar nome e ordem, desativar) e "Cargos" (nível de cada cargo). Verificar: `tools/testar_organograma.py`.

## 4. Documentação

- [x] 4.1 `docs/regras-de-negocio.md` (organograma e níveis) e `docs/domain-model.md` (nível hierárquico). Verificar: os documentos descrevem D1 a D5.
  - **Feito (13/10/2026):** `tools/testar_organograma.py` 33/33 cobre as tarefas 3.1 a 3.3.
