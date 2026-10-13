# Tasks

## 1. Backend

- [x] 1.1 `beneficio.links` (json) e descrição até 2000; tabela `beneficio_arquivo` (publicados à parte). Verificar: dry-run só com ADD_FIELD, UPDATE_FIELD e CREATE.
  - **Feito (13/10/2026):** UPDATE, ADD_FIELD e UPDATE_FIELD em `beneficio`; CREATE de `beneficio_arquivo`.
- [x] 1.2 `beneficios/{id}` PATCH e `beneficios` POST com descrição até 2000 e links (D3); `beneficios` GET e `meus_beneficios` GET com links e materiais. Verificar: `tools/checar_endpoints.py`.
  - **Feito (13/10/2026):** `beneficios/{id}` PATCH era da tarefa 85 e nunca tinha sido publicado (commit "WIP"); foi publicado agora, com os links. `beneficios/{id}/faq` POST, `beneficios/{id}/valores` POST e `beneficio_faq/*` continuam sem publicar (fora do escopo). A auditoria do PATCH passou a usar `valor_anterior` (o campo `valor_antigo` não existe na tabela).
- [x] 1.3 `beneficios/{id}/arquivos/envio` POST, `beneficios/{id}/arquivos` POST, `beneficio_arquivos/{id}/remover` POST e `beneficio_arquivos/{id}/abrir` GET (D1 e D2), auditados. Verificar: `tools/checar_endpoints.py`; envio e abertura no Supabase.
  - **Feito (13/10/2026):** `checar_endpoints` 223, 0 falhas. Envio e abertura por HTTP: não verificado (código por e-mail); as chamadas ao Supabase são as de `anexo-de-arquivos`, testadas em `docs/evidencias/anexo-de-arquivos.md`, com a pasta `beneficios/` no caminho.

## 2. Frontend

- [x] 2.1 Tela do colaborador (D4) e edição do RH (D5). Verificar: `tools/testar_beneficios.py`.
  - **Feito (13/10/2026):** 39/39.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/lgpd/operadores.md` (materiais de benefício no Supabase) e `docs/figma-pendencias.md`.
