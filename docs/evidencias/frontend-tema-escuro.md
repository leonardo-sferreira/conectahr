# Evidências — Tema claro e escuro (tarefa 63)

Seletor de tema no menu da conta, construído em 10/10/2026 no frontend Streamlit.

| Nó do Figma | O que é |
|---|---|
| 198:158 (claro), 315:2120 (escuro) | Menu da conta com "Tema: Claro / Escuro". Também nas cópias 197:330, 315:2062, 224:1272, 224:1472 e 224:1659 |
| 314:786 | Design System, bloco "Seletor de tema (claro e escuro)" |
| 294:622 | Design System, tokens do modo escuro, usados no código |

## Como funciona

**Onde fica.** O seletor fica no menu da conta, entre "Configurações" e "Sair da conta". A troca vale na hora,
para todas as telas da área logada e para o aviso de privacidade.

**Cores.** O código está em `frontend/theme.py`: `_ESCURO_CSS`, `tema_atual` e `render_topbar`. O tema escuro é uma
camada de CSS por cima do claro e só troca as cores, com os tokens do Design System:

| Elemento | Claro | Escuro |
|---|---|---|
| Card, modal e campo claro | branco | #22252C |
| Fundo e campo | #FAF9F6 | #16181D |
| Borda | #E4E3DF | #33363E |
| Texto | #16181D | #F2F2F0 |
| Texto secundário | #4B5563 | #A3A3AA |

O botão âmbar, os selos pastel e a sidebar não mudam.

**O que não muda.** A tela Entrar e o primeiro acesso continuam grafite nos dois temas, porque são o "crachá de
acesso" do protótipo.

**Como a escolha é lembrada.**
- Durante a sessão, a escolha fica em `st.session_state`.
- No navegador, fica num cookie de preferência: `crh_tema`, válido por 1 ano. O valor é sempre `claro` ou `escuro`;
  não tem dado pessoal nem identifica a pessoa.
- No próximo acesso pelo mesmo navegador, o app abre no tema escolhido.

## Como repetir

```
python tools/testar_privacidade_documentos.py   # 82 verificações, 7 delas do tema
```

**Resultado em 10/10/2026: 82 de 82.** O teste confere:
- o app abre no tema claro;
- "Escuro" troca o tema na hora e grava o cookie;
- o tema vale nas outras telas;
- "Claro" volta e regrava o cookie;
- a tela Entrar continua grafite;
- o aviso sem login segue o tema.

## Verificado no navegador (Chrome, API simulada)

- Ao trocar para "Escuro", o navegador ficou com o cookie `crh_tema=escuro`.
- Numa aba nova, um novo login abriu o Início direto no escuro.

Os prints estão em [`frontend-tema-escuro/`](frontend-tema-escuro/), só com dados fictícios:

| Print | Compare com |
|---|---|
| `1-menu-tema-claro` | 198:158 |
| `2-menu-tema-escuro` | 315:2120 |
| `3-inicio` | 108:870 |
| `4-configuracoes-privacidade` | 292:1418 |
| `5-modal-pedido` | — |
| `6-aviso-logado` | 292:1196 |
| `7-documentos` | 108:541 e 313:900 |
| `8-enviar-documento` | 313:1573 |
| `9-novo-acesso-lembra-o-tema` | — |

## Diferenças em relação ao Figma

- **Faixa do título:** no escuro, a faixa grafite do título se mistura ao fundo, como nas telas escuras do Figma
  (por exemplo, o Início 108:870).
- **Radio e campo de data:** a bolinha do radio e o calendário do campo de data são do próprio Streamlit e ficam
  com o tom escuro padrão dele.
