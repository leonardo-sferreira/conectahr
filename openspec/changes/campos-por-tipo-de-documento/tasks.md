# Tasks

## 1. Backend

- [x] 1.1 Campo `documento.dados` (json, opcional), publicado à parte. Verificar: dry-run só com ADD_FIELD.
  - **Feito (13/10/2026):** UPDATE + ADD_FIELD na tabela `documento`.
- [x] 1.2 `ConectaHR/validar_campos_documento` com o catálogo de D1 e as regras de D2 a D4; `documentos` POST chama a função e o `validar_cpf`, e grava `dados`; as leituras devolvem `dados`. Verificar: `tools/checar_endpoints.py` sem falha; a função rodada pela CLI com casos que passam e que falham.
  - **Feito (13/10/2026):** 21 casos em `docs/evidencias/campos-por-tipo-de-documento.md`; `checar_endpoints` 219, 0 falhas. `documentos` POST por HTTP: não verificado (código por e-mail).

## 2. Frontend

- [x] 2.1 Catálogo `documentos_modelo.CAMPOS`, validação da tela e o modal com os campos do tipo. Verificar: `tools/testar_privacidade_documentos.py`.
  - **Feito (13/10/2026):** 105/105.
- [x] 2.2 Conferência do RH com os dados informados. Verificar: `tools/testar_conferencia_documentos.py`.
  - **Feito (13/10/2026):** 53/53, nos modais de aprovar e recusar.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md` (seção 7), `docs/lgpd/registro-de-operacoes.md` (dados de F04) e `docs/figma-pendencias.md`. Verificar: descrevem D1 a D4.
