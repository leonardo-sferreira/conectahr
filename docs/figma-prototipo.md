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

## Handoff para Reflex

Este protótipo é a referência visual para a implementação real do frontend (tarefa
7.1, ainda não iniciada). A página Design System documenta os tokens e componentes
que devem ser reproduzidos no Reflex; as 13 telas do protótipo documentam o
conteúdo e a hierarquia de informação esperados em cada rota, alinhados à spec.md
real do projeto (não são telas genéricas — os status, campos e ações mostrados
batem com os enums e endpoints já implementados no backend).
