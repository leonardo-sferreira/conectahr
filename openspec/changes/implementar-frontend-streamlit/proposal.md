## Why

O backend do ConectaRH está praticamente pronto (75/83 tarefas do MVP `conectarh.gestao`), mas o frontend em Streamlit mal começou — só a tela de login existe, construída de forma incremental e ad-hoc, sem checklist de verificação nem registro formal das decisões de design. Já existe um protótipo Figma completo ("ConectaRH — Protótipo") com as 13 telas do sistema e um design system documentado (paleta, tipografia, componentes, estados obrigatórios, critérios de acessibilidade). Esta change formaliza a implementação de todo o frontend restante usando esse protótipo como **documento mestre**: tudo que existe no Figma deve existir no Streamlit, e o design system dele é o padrão obrigatório — não uma referência solta.

## What Changes

- Adotar o protótipo Figma ("ConectaRH — Protótipo", arquivo `fph1M5tB4rA4gqfIysSmkn`) como fonte de verdade visual e funcional do frontend: toda tela e fluxo definido lá deve ter uma implementação correspondente no Streamlit, e qualquer divergência entre o app e o Figma é tratada como bug (não como variação aceitável).
- Implementar as 13 telas do protótipo como páginas/estados do app Streamlit: Login e Código de Acesso (já implementadas nesta sessão), Início, Central de Pendências, Perfil, Pagamento, Onboarding, Ponto, Férias, Documentos, Auditoria, Regras, Trajetória.
- Extrair o design system do Figma (paleta grafite `#16181D` + âmbar `#F5A623`, tipografia Sora/Manrope, o componente "crachá de acesso", a "trilha de conexão") para um tema reutilizável (`frontend/theme.py`), documentando os tokens exatos em vez de aproximá-los de memória.
- Implementar de forma consistente entre todas as telas os 6 estados de UI exigidos pelo design system: carregando, vazio, sucesso, erro, bloqueado e permissão negada.
- Integrar cada tela de verdade com os endpoints já implementados no backend (ver `docs/regras-de-negocio.md`), seguindo o padrão de execução em três etapas por tela: UI → Integração → Teste.
- Aplicar os critérios de acessibilidade documentados no Figma (contraste WCAG, foco visível, cor nunca como único indicador, navegação por teclado) — corresponde à tarefa 7.10 do change `conectarh.gestao`.
- **Antes** de implementar qualquer elemento do Figma que o Streamlit não suporte nativamente (ex.: interações de arrastar-e-soltar, animações complexas, visualizações muito customizadas), identificar isso explicitamente nesta change (seção correspondente do `design.md`, atualizada conforme cada tela for iniciada) e indicar a tecnologia alternativa proposta (ex.: componente customizado via `streamlit.components.v1`, biblioteca JS embutida) **antes** de implementar — nunca entregar uma versão silenciosamente degradada sem avisar.

## Capabilities

### New Capabilities

- `conectahr`: comportamento observável do frontend do ConectaRH (telas, navegação, estados de UI, fidelidade ao design system do Figma). O backend deste mesmo domínio já está sendo especificado pela change `conectarh.gestao` (ainda não arquivada, sem conflito de arquivo porque cada change mantém sua própria pasta `specs/` até ser arquivada) — esta change cobre especificamente o comportamento do frontend construído sobre esse backend, sem duplicar as regras de negócio já documentadas em `docs/regras-de-negocio.md`.

### Modified Capabilities

Nenhuma — ver nota acima sobre a capability `conectahr`.

## Impact

- Novo conteúdo em `frontend/`: hoje só existe a tela de login (`app.py`, `theme.py`, `api_client.py`, `assets/logo-icon.svg`); esta change adiciona as 11 telas restantes e amplia o tema/design system reutilizável.
- Nenhuma mudança no backend (Xano) — consumo exclusivo dos endpoints já implementados e documentados.
- Fecha a tarefa 7.1 ("Criar telas e endpoints dos fluxos por fatia vertical") e contribui para a 7.10 (acessibilidade) do change `conectarh.gestao`.
- Referência de design: protótipo Figma "ConectaRH — Protótipo" (`fph1M5tB4rA4gqfIysSmkn`), incluindo a página "Design System" (tokens, componentes, estados) e a versão "Protótipo — Dark".
