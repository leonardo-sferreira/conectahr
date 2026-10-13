# Tasks

## 1. Figma

- [x] 1.1 Aba Cargos (500:1156) com "Novo cargo", colunas Cargo, Senioridade, Departamento, Nível e Pessoas, "Editar"; modal "Novo cargo" com o nome que vai para a carteira. Verificar: prints dos nós.
  - **Feito (13/10/2026):** aba Cargos 500:1156 e modal "Novo cargo" 502:852.

## 2. Backend

- [x] 2.1 `cargo.senioridade` e `cargo.departamento_id` (schema publicado à parte). Verificar: dry-run só com ADD_FIELD.
- [x] 2.2 `cargos` POST e `cargos/{id}` PATCH com senioridade e departamento (POST também com nível); `organograma` GET com departamento e senioridade dos cargos. Verificar: `tools/checar_endpoints.py` sem falha; por HTTP, Colaborador recebe 403 ao cadastrar cargo (não verificado sem o código por e-mail).
  - **Feito (13/10/2026):** campos publicados à parte (2 ADD_FIELD); `cargos` POST e PATCH passaram a auditar, sem o salário; `checar_endpoints` 218, 0 falhas. Teste por HTTP: não verificado.

## 3. Frontend

- [x] 3.1 Regras dos cargos (título com a senioridade, nome-base na edição, validação, cargos do departamento). Verificar: `tools/testar_cargos.py`.
- [x] 3.2 Aba Cargos com "Novo cargo" e "Editar" (nome, senioridade, departamento, nível, salário, descrição) e a lista com senioridade e departamento. Verificar: `tools/testar_cargos.py` com AppTest.
- [x] 3.3 Admissão com os cargos do departamento escolhido. Verificar: `tools/testar_cargos.py` e `tools/testar_cadastro.py`.

## 4. Documentação

- [x] 4.1 `docs/regras-de-negocio.md` e `docs/domain-model.md` (cargo com senioridade e departamento). Verificar: descrevem D1 a D5.
  - **Feito (13/10/2026):** `tools/testar_cargos.py` 16/16 cobre 3.1 a 3.3; `tools/testar_cadastro.py` 52/52 e `tools/testar_organograma.py` 32/32.
