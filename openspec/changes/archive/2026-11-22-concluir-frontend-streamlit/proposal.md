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
- Em 10 e 11/10/2026, o uso das telas trouxe pedidos que mudam o comportamento do sistema, com backend
  novo ou alterado. Eles entraram nesta change como as tarefas 77 a 83:
  - vincular uma conta de acesso a uma ficha de colaborador (Admin e RH também batem ponto);
  - espelho de ponto mensal, com correção de qualquer dia, inclusive sem marcação, e falta injustificada;
  - superior direto na ficha e hierarquia nas decisões de ponto, férias e ausências, para qualquer perfil;
  - folha de ponto da equipe e do RH, com ajuste direto auditado;
  - prazo, definido pelo RH, para pedir correção de ponto;
  - benefícios: catálogo do RH e vínculo por pessoa.

## Regras que continuam valendo

- O frontend é construído **só** a partir do protótipo do Figma; tela nova é desenhada antes
  (`AGENTS.md`, seção 6, e `frontend/AGENTS.md`).
- A autorização é sempre do backend.
- Depois de cada tela: teste dos 6 estados e do escopo por perfil, com evidência em `docs/evidencias/`.

## Capabilities

### Modified Capabilities

- `conectahr`: altera "Autorização por perfil e estrutura organizacional", "Registro de ponto e correção",
  "Férias e ausências", "Central de tarefas e pendências" e "Base de conhecimento do RH"; acrescenta
  "Espelho de ponto mensal", "Folha de ponto da equipe e do RH", "Prazo para pedir correção de ponto",
  "Benefícios do colaborador" e "Vínculo de conta a ficha de colaborador".

## Impact

- **Telas:** o comportamento esperado continua nos requisitos "Cobertura das telas do protótipo Figma" e
  "Protótipo Figma como fonte única do frontend" da spec principal.
- **Spec:** as tarefas 77 a 83 mudaram regras e o backend. Até 11/10/2026 a change declarava
  `skip_specs: true` e "nenhuma mudança de backend"; a spec foi escrita depois da implementação (tarefa 84),
  a partir do que foi publicado e testado.
- **Backend (Xano):**
  - tabelas novas: `beneficio`, `colaborador_beneficio` e `configuracao`;
  - campo novo: `colaborador.superior_colaborador_id`;
  - endpoints novos de folha de ponto, prazo de correção, benefícios, superior e vínculo de conta;
  - endpoints alterados de decisão de férias, ausências e correções de ponto, e da central de tarefas.
  O detalhe está em `docs/regras-de-negocio.md`.
- **Figma:** as telas feitas com o Figma fora do ar precisam ser desenhadas lá (lista no `design.md`).
