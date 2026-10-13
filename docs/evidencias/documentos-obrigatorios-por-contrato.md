# Documentos obrigatórios por contrato (change `documentos-obrigatorios-por-contrato`)

**Data:** 13/10/2026. **Como:** funções rodadas no Xano pela CLI (`xano function run`), com dados fictícios.

## Carga das regras (`ConectaHR/semear_documentos_obrigatorios`)

| Cenário | Esperado | Obtido |
|---|---|---|
| Primeira carga | 38 regras criadas (9 de CLT, 9 de Temporário, 9 de Aprendiz, 5 de Estágio, 5 de PJ e 1 de responsável legal para menores) | 38 criadas, 0 já existiam |
| Segunda carga | Nenhuma regra nova | 0 criadas, 38 já existiam |

## Campos dos tipos novos (`ConectaHR/validar_campos_documento`)

| Cenário | Esperado | Obtido |
|---|---|---|
| Título de eleitor com 12 dígitos (com espaços), zona, seção e UF em minúsculas | Aceito; UF em maiúsculas | Igual |
| Título com 11 dígitos | Recusado (12 dígitos) | Igual |
| Título sem seção | "Informe a zona e a secao eleitoral." | Igual |
| Certidão de casamento | Aceita | Igual |
| Certidão sem o tipo | Recusada | Igual |
| Termo de estágio completo | Aceito | Igual |
| Termo sem a apólice do seguro | Recusado | Igual |
| Termo sem o fim | Recusado | Igual |
| Termo com início no futuro | Aceito (o termo é assinado antes do início) | Igual |
| Cartão CNPJ com pontuação e razão social | Aceito | Igual |
| CNPJ com 13 dígitos | Recusado | Igual |
| Contrato social de MEI | Aceito | Igual |
| Contrato social de "cooperativa" | Tipo de empresa inválido | Igual |
| RG (tipo antigo) depois da mudança | Aceito como antes | Igual |

## Não verificado

- `colaboradores/{id}/documentos_pendentes_obrigatorios` GET por HTTP (RG e CIN equivalentes): precisa do código de acesso por e-mail.
