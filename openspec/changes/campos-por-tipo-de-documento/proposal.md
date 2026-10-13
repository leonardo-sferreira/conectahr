# Proposal

## Why

O modal "Enviar documento" pede os mesmos campos para todo tipo (número, data de emissão e arquivo). O RG tem órgão emissor e UF, a CNH tem categoria e validade, o CPF não tem data, o comprovante de residência não tem número. O usuário pediu (13/10/2026) que cada tipo peça só os campos dele, validados, para que o RH confira o que a pessoa digitou contra o arquivo enviado. Hoje a conferência do RH nem mostra os dados digitados.

## What Changes

- **Catálogo de campos por tipo** (D1): cada um dos 15 tipos que a pessoa envia tem os seus campos, obrigatórios ou opcionais. Ao escolher o tipo no modal, aparecem só os campos dele.
- **Validação no backend** (`ConectaHR/validar_campos_documento`, chamada por `documentos` POST): campos obrigatórios por tipo, UF válida, opções fechadas (categoria da CNH, resultado do ASO, nível de escolaridade, vínculo do responsável), datas sem futuro, validade depois da emissão, CNH com 11 dígitos, comprovante de residência dos últimos 90 dias e CPF com dígitos verificadores (o do tipo CPF e o da CIN conferidos com o CPF da ficha).
- **Campo `documento.dados`** (json) para o que não cabe nas colunas atuais (órgão emissor, categoria, série, CRM, curso, instituição, conselho e outros), montado só com as chaves do tipo.
- **Conferência do RH** mostra os dados informados ao lado do arquivo, nos modais de aprovar e recusar.

## Non-goals

- `documentos/{id}` PATCH (nenhuma tela usa) e o holerite e o informe do RH continuam como estão.
- Leitura automática do arquivo (OCR) e consulta à Receita: o RH confere a olho, com o arquivo aberto.
- Desenho no Figma: fica registrado em `docs/figma-pendencias.md` (decisão do usuário de deixar o Figma para depois).

## Impact

- Backend: `table/documento.xs` (campo `dados`), `function/conectahr/validar_campos_documento.xs` (nova), `api/conecta_rh_documentos/documentos_POST.xs`, `documentos_GET.xs`, `documentos/id_GET.xs`, `meus_documentos_GET.xs`.
- Frontend: `documentos_modelo.py`, `pagina_documentos.py`, `conferencia_modelo.py`, `pagina_conferencia_documentos.py`.
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/registro-de-operacoes.md`, `docs/figma-pendencias.md`.
