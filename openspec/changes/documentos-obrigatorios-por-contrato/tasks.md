# Tasks

## 1. Backend

- [x] 1.1 Cinco tipos novos nos enums de `documento`, `documento_obrigatorio_regra` e `pendencia_documento` (schema publicado à parte) e nas validações dos endpoints. Verificar: dry-run só com UPDATE_FIELD.
  - **Feito (13/10/2026).**
- [x] 1.2 Campos dos tipos novos em `validar_campos_documento` (D4). Verificar: função rodada pela CLI.
  - **Feito (13/10/2026):** 14 casos em `docs/evidencias/documentos-obrigatorios-por-contrato.md`.
- [x] 1.3 `semear_documentos_obrigatorios` (D1 e D2) e RG/CIN equivalentes (D3). Verificar: primeira carga cria as 38 regras; a segunda não cria nenhuma.
  - **Feito (13/10/2026):** 38 criadas; na segunda, 0 criadas e 38 já existiam. `checar_endpoints` 223, 0 falhas. Pendentes obrigatórios por HTTP: não verificado (código por e-mail).

## 2. Frontend

- [x] 2.1 Nomes e campos dos tipos novos; regras agrupadas por contrato na aba do RH. Verificar: `tools/testar_privacidade_documentos.py` e `tools/testar_conferencia_documentos.py`.
  - **Feito (13/10/2026):** 108/108 e 54/54.

## 3. Documentação

- [x] 3.1 `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md` e a evidência.
