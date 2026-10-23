# Design

## Context

Ver proposal.md. O menu é desenhado em `app.py`, com `st.button` por item, e o CSS do tema dá o visual da barra. O Streamlit não tem um grupo recolhível com esse visual: `st.expander` mudaria o layout. Por isso o cabeçalho é um botão com o estilo do rótulo de grupo que já existia.

## Decisions

### D1. Cabeçalho do grupo

- `st.button(nome, key="navgrupo_<nome>")` dentro de um container com a chave `grpfechado_<nome>` ou `grpaberto_<nome>`. A chave do container diz ao CSS para onde a seta aponta.
- **A seta é feita com duas bordas no `::after`**, porque a fonte Manrope não tem os glifos ▸ e ▾. Aponta para a direita fechada e para baixo aberta, alinhada à direita.
- O texto tem o mesmo estilo do antigo rótulo de grupo: 11 px, maiúsculas e cinza.

### D2. Estado

- `st.session_state.menu_grupos` guarda `{grupo: aberto}`. Ausente quer dizer fechado, então tudo começa fechado.
- Clicar no cabeçalho inverte só aquele grupo: os grupos são independentes.
- **Ao chegar numa tela** (`menu_pagina` mudou), o grupo que contém o item ativo abre. Depois, a pessoa pode fechá-lo mesmo estando na tela.

### D3. Itens

- **Menu principal:** os 13 itens, iguais para todos.
- **RH (RH e Admin):** os 15 de antes, mais Auditoria e Regras no fim.
- **Equipe:** completo para o Gestor; para quem é superior direto, só "Folha de ponto da equipe" e "Metas da equipe", como antes.
- **Admin:** só para o Admin.
- **"Denúncias":** continua solto, só para a comissão de ética.

### D4. Testes

- `tools/testar_menu.py` cobre:
  - os grupos por perfil, começando fechados;
  - abrir e fechar, independentes;
  - a abertura automática pela tela;
  - Auditoria e Regras no RH.
- **Os outros testes conferem itens de grupo.** Eles passam a começar com os grupos abertos (`menu_grupos` no ajudante), para continuar conferindo o que sempre conferiram.

## Risks

- **Quem procura Auditoria ou Regras no menu principal** agora acha no grupo RH. A tela aberta abre o grupo, então quem chega por um atalho não se perde.
