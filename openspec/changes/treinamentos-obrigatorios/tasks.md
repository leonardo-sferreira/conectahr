# Tasks

## 0. Figma

- [x] 0.1 Desenhar a seção 22 (549:1319): matriz do RH (549:1321), modais "Novo treinamento" (550:1325) e "Registrar conclusão" (550:1370) e "Meus treinamentos" (550:1415) (D5). Verificar: prints dos nós.
  - **Feito (20/10/2026):** modo claro. Falta a versão escura (docs/figma-pendencias.md).

## 1. Backend

- [x] 1.1 Tabelas `treinamento` e `treinamento_conclusao` (D1). Verificar: dry-run só com `CREATE`.
  - **Feito (20/10/2026):** publicadas.
- [x] 1.2 `treinamentos` GET e POST, `treinamentos/{id}` PATCH, `treinamentos/{id}/conclusoes` e `meus_treinamentos` (D2 a D4). Verificar: `checar_endpoints` e dry-run só com `CREATE`.
  - **Feito (20/10/2026):** publicados; `checar_endpoints` 270, 0 falhas.
- [ ] 1.3 Rodar `tools/testar_conformidade_http.py` com login (conta do RH ou Admin) e registrar uma conclusão de teste para conferir a validade calculada.

## 2. Frontend

- [x] 2.1 `api_client.py` e `treinamentos_modelo.py`. Verificar: regras em `tools/testar_treinamentos.py`.
- [x] 2.2 "Treinamentos" do RH e "Meus treinamentos" (D5). Verificar: `tools/testar_treinamentos.py`.
  - **Feito (20/10/2026):** 22/22.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 21), `docs/lgpd/registro-de-operacoes.md` (F12 e cobertura) e `docs/figma-pendencias.md`. Verificar: `openspec validate treinamentos-obrigatorios`.
