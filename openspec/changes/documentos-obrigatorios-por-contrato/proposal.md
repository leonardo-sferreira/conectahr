# Proposal

## Why

A matriz de documentos obrigatórios (`documento_obrigatorio_regra`) existia vazia: o RH teria de montar, regra por regra, o que pedir em cada admissão. O usuário pediu (13/10/2026) que o sistema venha com essa definição pronta, a partir de uma pesquisa, para CLT, estágio, PJ e os demais contratos. Faltavam também tipos de documento comuns na admissão (título de eleitor, certidão, termo de compromisso de estágio, cartão CNPJ e contrato social).

## What Changes

- **Cinco tipos novos de documento:** título de eleitor, certidão de nascimento ou casamento, termo de compromisso de estágio, cartão CNPJ e contrato social (ou CCMEI), com os campos de cada um (como na change `campos-por-tipo-de-documento`).
- **38 regras pré-definidas** por tipo de contrato (D1), cadastradas por `ConectaHR/semear_documentos_obrigatorios`, que pode ser rodada de novo sem duplicar nem mexer no que o RH cadastrou.
- **RG e CIN equivalentes** na lista de pendentes obrigatórios: a CIN substitui o RG.
- A aba "Obrigatórios por cargo" do RH mostra as regras agrupadas por contrato, os obrigatórios antes dos opcionais.

## Non-goals

- Regras por cargo (CNH para motorista, registro no conselho para profissões regulamentadas): ficam para o RH cadastrar, porque os cargos são de cada empresa.
- Documentação migratória e laudo de deficiência: dependem de dados que a ficha não tem (nacionalidade, deficiência); o RH pede por pendência.
- Gerar pendências automáticas na admissão a partir das regras.

## Impact

- Backend: enums de `documento`, `documento_obrigatorio_regra` e `pendencia_documento`; `validar_campos_documento`; `documentos` POST, `documentos/{id}` PATCH, `documentos_obrigatorios` POST, `pendencias_documento` POST, `catalogos` GET, `colaboradores/{id}/documentos_pendentes_obrigatorios` GET; função nova `semear_documentos_obrigatorios`.
- Frontend: `onboarding_modelo.TIPOS_DOCUMENTO`, `documentos_modelo.CAMPOS`, `pagina_documentos.py`, `conferencia_modelo.linhas_regras`.
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`, `docs/evidencias/`.
