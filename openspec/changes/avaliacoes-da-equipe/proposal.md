# Avaliações da equipe — F15 com os contratos atuais

## Why

O item do menu do Gestor ainda está em construção. O backend já permite ao avaliador
designado responder e enviar avaliações, mas não oferece ao Gestor o fluxo completo de
contestações desenhado no F15. Implementar somente o caminho autorizado pelo usuário.

## What Changes

- Página Streamlit e navegação para as avaliações atribuídas ao usuário, com relação `gestor`.
- Seleção de ciclo, indicadores verificáveis, competências, rascunho de respostas e envio.
- Autoavaliação e contestações indisponíveis, sem inferir estados ou contagens.
- Testes locais com API simulada e registro explícito das verificações ainda pendentes.
- Nenhuma alteração de backend, endpoint, dado ou configuração local do MCP.

## Capabilities

### New Capabilities

Nenhuma capability separada: extensão do módulo `conectahr`.

### Modified Capabilities

- `conectahr`: consulta e preenchimento das avaliações atribuídas ao Gestor no F15.

## Impact

Frontend, testes e documentação. Reutiliza os endpoints existentes de ciclos, avaliações
próprias, competências, respostas e envio; organograma apenas para nome/cargo/nível.
