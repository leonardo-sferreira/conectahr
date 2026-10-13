# Campos por tipo de documento (change `campos-por-tipo-de-documento`)

**Data:** 13/10/2026. **Como:** `ConectaHR/validar_campos_documento` publicada no Xano e rodada pela CLI
(`xano function run`), com dados fictícios (o CPF 529.982.247-25 é um número de exemplo válido).

| Cenário | Esperado | Obtido |
|---|---|---|
| RG completo, UF e órgão em minúsculas, com uma chave a mais em `dados` | Aceito; UF e órgão em maiúsculas; a chave a mais descartada | Igual (`dados` = só `orgao_emissor`) |
| RG sem órgão emissor | "Informe o orgao emissor." | Igual |
| RG com UF "XX" | UF inválida | Igual |
| CPF com data de emissão | Aceito; a data é descartada (o CPF não tem data); CPF devolvido para conferir | Igual |
| CNH sem validade | "Informe a validade." | Igual |
| CNH com 10 dígitos e com letra | "O numero de registro da CNH tem 11 digitos." | Igual nos dois |
| CNH com categoria "Z" | Categoria inválida | Igual |
| CNH com pontos e traço e categoria "ab" | Aceita; categoria "AB" | Igual |
| Reservista com emissão em 2030 | Data futura recusada | Igual |
| Comprovante de residência de 01/01/2026 | Recusado (mais de 90 dias) | Igual |
| Comprovante de residência de 01/10/2026 com número | Aceito; o número é descartado | Igual |
| ASO com resultado "Inapto" e CRM | Aceito; resultado "inapto" | Igual |
| ASO com resultado "talvez" | Recusado | Igual |
| Escolaridade sem instituição | "Informe a instituicao." | Igual |
| Responsável legal completo | Aceito; CPF do responsável devolvido para conferir | Igual |
| Responsável legal sem CPF | "Informe o CPF do responsavel." | Igual |
| Documentação migratória com validade antes da emissão | Recusada | Igual |
| Outro sem descrição | "Informe que documento e." | Igual |
| CTPS digital só com o número | Aceita | Igual |

`tools/testar_privacidade_documentos.py` (105/105) e `tools/testar_conferencia_documentos.py` (53/53) cobrem a tela.

## Não verificado

- `documentos` POST por HTTP com login (CPF diferente da ficha, recusa da função e gravação de `dados`): precisa do
  código de acesso por e-mail. A função e o `validar_cpf` são os mesmos testados acima; o padrão de mensagem vinda
  da função (`error = $...`) já é usado em `colaboradores` POST.
