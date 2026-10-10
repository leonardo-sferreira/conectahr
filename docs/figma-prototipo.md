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
- **Protótipo — Dark**: as 13 telas originais em modo escuro, com navegação própria
  religada internamente, mais as seções 5, 9 a 12 e 13 a 17 em modo escuro. Ainda só em
  modo claro: as seções 1 a 4 e 6 a 8 e a página de fluxos.
- **Fluxos — apresentação**: os fluxos F01 a F39, uma seção por fluxo, com as etapas
  de cada caminho, um índice e um grupo por perfil. Há dois "F37" (Regras e Onboarding);
  a renumeração está na tarefa 69 da change `concluir-frontend-streamlit`.

**Atualização de 09/10/2026.** A página "ConectaRH — Protótipo" passou a ter seções
numeradas de 0 a 17 (as seções 6 a 12 cobrem Perfil, menus por perfil e as áreas de RH,
Gestor e Admin). As seções 13 a 16 trazem as telas que a spec exigia e faltavam: aviso de
privacidade e exportação de dados, Regras (criar, aprovar, simular, aplicar), Rotina diária
com Retenção e anonimização, e Reconhecimentos. A seção 17 (10/10/2026) redesenha o
Onboarding do primeiro acesso com as 13 etapas do backend. O mapa de nós está no `design.md` da change
`concluir-frontend-streamlit`. O quadro "Design System — Modo escuro e componentes" documenta
os tokens do modo escuro e os componentes novos; o quadro "Senha, onboarding e menu"
documenta o campo de senha com o olho, o menu por grupo de perfil e as etapas do onboarding.

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
