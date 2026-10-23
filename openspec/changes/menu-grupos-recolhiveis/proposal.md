# Proposal

## Why

O usuário pediu (23/10/2026) para melhorar a leitura do menu lateral sem mudar o visual. O Admin vê 33 itens de uma vez, e o RH vê 29. A lista não cabe na tela e obriga a rolar para achar o grupo certo.

## What Changes

- **Grupos recolhíveis:** "RH", "Equipe" e "Admin" viram cabeçalhos clicáveis com uma seta. Fechado, o grupo mostra só o nome; aberto, mostra os itens embaixo.
- **Decisões do usuário:**
  - os grupos começam fechados;
  - cada grupo abre e fecha independente dos outros;
  - Auditoria e Regras saem do menu principal e vão para o grupo RH.
- **O grupo da tela aberta abre sozinho** quando a pessoa chega nela; a escolha fica guardada na sessão.
- **O menu principal** fica igual para todos os perfis. O Colaborador não tem grupo nenhum, então nada muda para ele.

## Non-goals

- Mudar o visual da barra lateral (cor, largura, logo, itens): pedido explícito do usuário.
- Guardar a escolha entre sessões (cookie ou banco): a sessão basta.
- Mudar quem vê o quê. A lista de itens por perfil continua só uma conveniência; a autorização é do backend.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: menu lateral com grupos recolhíveis por perfil.

## Impact

- **Frontend:** `app.py` (ajudantes `_item_menu` e `_grupo_menu`, e o estado `menu_grupos` na sessão) e `theme.py` (o cabeçalho do grupo e a seta).
- **Figma:** seção 24 (567:862), com três estados: Admin com tudo fechado, Admin em "Treinamentos" com o RH aberto e Gestor com a Equipe aberta.
- **Testes:**
  - novo `tools/testar_menu.py`;
  - os outros testes abrem os grupos no ajudante que monta o app, porque conferem itens de grupo.
- **Backend:** nenhum.
