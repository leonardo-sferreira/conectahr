# Proposal

## Why

A change `concluir-mvp-conectarh` fechou o backend, a segurança, a LGPD e a documentação. Sobraram as
tarefas de **frontend** (telas do Streamlit) e cinco pendências que dependem delas ou da hospedagem. Elas
não bloqueiam a spec nem a documentação, mas não podem sumir: esta change as recebe, com a origem de cada
uma, para a `concluir-mvp-conectarh` poder ser arquivada.

## What Changes

- Recebe 57 tarefas abertas da `concluir-mvp-conectarh`:
  - 1.3 (telas por fatia vertical), 1.4 (publicar o frontend e o teste de fumaça), 1.7 (acessibilidade),
    3.50 (fontes locais) e 4.19 (tela "Privacidade");
  - as 52 tarefas da seção 2 (telas do Figma, painel de notificações, configurações e as
    telas que ainda precisam ser desenhadas).
- Cada tarefa leva, entre parênteses, a numeração original.
- Em 09/10/2026 o Figma foi conferido e a lista de "telas a desenhar" estava desatualizada: quase tudo
  já existia. As telas que faltavam (aviso de privacidade, Regras com criar/aprovar/simular/aplicar, Rotina
  diária, Retenção e anonimização, Reconhecimentos) foram desenhadas em modo claro e escuro. A seção 3 do
  `tasks.md` (tarefas 58 a 67) registra isso e as pendências que o levantamento encontrou.

## Regras que continuam valendo

- O frontend é construído **só** a partir do protótipo do Figma; tela nova é desenhada antes
  (`AGENTS.md`, seção 6, e `frontend/AGENTS.md`).
- A autorização é sempre do backend.
- Depois de cada tela: teste dos 6 estados e do escopo por perfil, com evidência em `docs/evidencias/`.

## Impact

Nenhuma mudança de spec nem de backend: `skip_specs: true`. O comportamento esperado de cada tela já
está nos requisitos "Cobertura das telas do protótipo Figma" e "Protótipo Figma como fonte única do
frontend" da spec principal.
