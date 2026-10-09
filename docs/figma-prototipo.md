# Protótipo Figma — ConectaRH

O protótipo visual do ConectaRH vive inteiramente no Figma (arquivo colaborativo,
conta de estudante do time) — não existe arquivo `.fig` nem export nenhum
versionado neste repositório, o link abaixo é a fonte de verdade.

**Arquivo:** https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn

## Páginas

- **ConectaRH — Protótipo**: 13 telas navegáveis, cobrindo os fluxos da tarefa 7.13
  (login em 2 passos, central de pendências, onboarding, ponto, férias, documentos,
  auditoria, regras) mais telas adicionais criadas ao longo da iteração — início,
  perfil, pagamento (holerite/informe de rendimentos), trajetória (avaliação
  360/carreira). Fluxo de cliques completo: login → início, e todas as telas
  interligadas pelo menu lateral e pelo chip do usuário. Abrir em modo **Present**
  a partir da tela de login navega o protótipo inteiro.
- **Design System**: tokens de cor, tipografia (Sora/Manrope), espaçamento, grid,
  componentes (botão, badge, input, item de navegação, trilha de conexão) e os 6
  estados exigidos pela tarefa 1.11 (carregando, vazio, sucesso, erro, bloqueado,
  permissão negada), com critérios de acessibilidade documentados (contraste WCAG,
  foco visível, cor nunca sozinha, navegação por teclado).
- **Protótipo — Dark**: as mesmas 13 telas em modo escuro, com navegação própria
  religada internamente.

## Identidade visual

Paleta grafite (#16181D) + âmbar (#F5A623) como acento único, escolhida após
iteração com o time sobre a direção visual (uma paleta roxo/azul foi testada
primeiro e substituída). Dois elementos de assinatura reaproveitados em todas as
telas: o "crachá de acesso" no login (card com clipe, sobre fundo gradiente/sólido)
e a "trilha de conexão" (pontos ligados por linha — âmbar para itens em aberto,
verde para resolvidos) nas listas de pendências, férias, documentos, avaliações e
regras.

## Handoff para Streamlit

**Protótipo oficial:** https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn

O frontend é feito em Streamlit (`frontend/`). Este protótipo é a referência visual e de
conteúdo; a página Design System documenta os tokens e os componentes a reproduzir, e as
telas mostram a hierarquia de informação de cada rota, alinhada aos status, campos e ações
que o backend já implementa. O mapa de seções e nós está em `design.md` (C3) da change
`concluir-mvp-conectarh`.

Regras de implementação:

- **O Figma é desenhado antes.** Tela nova só é construída depois de existir no protótipo.
  Antes de codar, buscar o nó da tela e conferir o que ele mostra.
- **Estados de interface:** toda tela trata os 6 estados do Design System (carregando, vazio,
  sucesso, erro, bloqueado, permissão negada).
- **Alertas dentro do card:** os avisos de erro e de sucesso ficam dentro do card, abaixo do
  título, como no Figma.
- **Fontes e cores:** Sora e Manrope, com os tokens do Design System (ver `frontend/theme.py`).
- **Acessibilidade:** contraste, foco visível, cor nunca sozinha e navegação por teclado.
- **O frontend não é mecanismo de segurança.** Perfil e escopo são sempre aplicados pelo
  backend; esconder um botão não substitui a regra.
