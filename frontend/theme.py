"""
Tema visual do ConectaRH — extraído do protótipo Figma real (arquivo
"ConectaRH — Protótipo", fph1M5tB4rA4gqfIysSmkn, nós 28:27 e 31:6).

Streamlit não permite estilização pixel-perfect nativa, então usamos CSS
injetado via st.html() para reproduzir os tokens de design (cor, tipografia,
o "crachá de acesso") o mais fiel possível. IMPORTANTE (achados confirmados
lendo o bundle JS do Streamlit, inspecionando o DOM ao vivo via Chrome
DevTools Protocol, e testando a sanitização em isolado com o DOMPurify real
no navegador — não por tentativa e erro):

st.html() SEMPRE sanitiza com DOMPurify, mesmo sem passar por st.markdown.
Consequências práticas:
- A tag de estilo só sobrevive com unsafe_allow_javascript=True (só então o
  Streamlit inclui ela e a de script no ADD_TAGS do DOMPurify) E só se o
  conteúdo enviado não for *apenas* essa tag isolada (nesse caso o próprio
  Streamlit desvia para um "event container" que não chega a aplicar como
  CSS de página) — daí o marcador `<div id="crh-styles-marker">` antes do
  bloco de estilo abaixo.
- SVG inline é removido inteiramente (o profile do DOMPurify usado é só
  "html", sem "svg") - por isso o ícone do logo vira
  `<img src="data:image/svg+xml;base64,...">` em vez de SVG cru.
- Causa raiz do bloco de estilo inteiro ser removido (isolada por bissecção
  testando o DOMPurify real, via CDN, com a mesma config do Streamlit):
  NÃO é o seletor `:has()` (testado isolado, sobrevive normalmente). É a
  simples presença da substring literal da própria tag de estilo (ex.: em
  texto de comentário dentro do CSS, mesmo dentro de `/* ... */`) em
  qualquer lugar do conteúdo — o DOMPurify trata isso como sinal de
  aninhamento suspeito (proteção contra mXSS) e descarta o elemento inteiro.
  Por isso os comentários deste arquivo evitam mencionar o nome da tag entre
  `< >` literalmente.
- O card usa `st.container(key="crh_card")` em vez de um marcador com
  `:has()`: não por causa da sanitização, mas porque é o mecanismo que o
  próprio Streamlit documenta para dar identidade CSS estável a um
  container (`st-key-crh_card`), e porque a versão instalada do Streamlit
  (1.64) não usa mais o wrapper `data-testid="stVerticalBlockBorderWrapper"`
  de versões antigas — a classe de key cai direto no
  `div[data-testid="stVerticalBlock"]` do container.

Qualquer nova tela deve importar e reutilizar isto em vez de redefinir
estilo do zero.
"""

import base64
import html
from pathlib import Path

import streamlit as st

# Tokens extraídos do Figma (docs/figma-prototipo.md + inspeção direta dos nós).
GRAFITE = "#16181D"
GRAFITE_SECUNDARIO = "#4B5563"
AMBAR = "#F5A623"
AMBAR_ESCURO = "#D9860F"
MARFIM = "#FAF9F6"
BORDA = "#E4E3DF"
CINZA_CLARO = "#B2B5BA"
AMBAR_BG = "#FEF3C7"
SUCESSO = "#16A34A"
ERRO = "#DC2626"

_ASSETS_DIR = Path(__file__).parent / "assets"
_LOGO_ICON_SVG_BYTES = (_ASSETS_DIR / "logo-icon.svg").read_bytes()
# SVG inline e removido pelo DOMPurify de st.html() (profile so "html", sem
# "svg") - por isso vira <img> com data URI em vez de <svg> cru.
_LOGO_ICON_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(_LOGO_ICON_SVG_BYTES).decode("ascii")
# Sino de notificações da barra superior (asset exportado do nó 62:64).
_BELL_SVG = (_ASSETS_DIR / "bell.svg").read_text(encoding="utf-8")
_BELL_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(_BELL_SVG.encode("utf-8")).decode("ascii")
# Sino no modo escuro (Figma 108:870): caixa #22252C, borda #33363E e traço #F2F2F0.
_BELL_ESCURO_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(
    _BELL_SVG.replace('fill="white"', 'fill="#22252C"').replace('stroke="#E4E3DF"', 'stroke="#33363E"')
    .replace('stroke="#16181D"', 'stroke="#F2F2F0"').replace('stroke="white"', 'stroke="#22252C"').encode("utf-8")
).decode("ascii")

_BASE_CSS = f"""
<style>
  /* Fontes servidas pelo próprio app (frontend/static/fonts, licença OFL), e não pelo Google Fonts:
     assim o navegador de quem usa não manda o IP ao Google (tarefa 4, LGPD). O caminho é relativo à
     página e precisa de server.enableStaticServing = true em .streamlit/config.toml. */
  @font-face {{ font-family: 'Sora'; font-style: normal; font-weight: 600; font-display: swap; src: url('app/static/fonts/sora-600.woff2') format('woff2'); }}
  @font-face {{ font-family: 'Sora'; font-style: normal; font-weight: 800; font-display: swap; src: url('app/static/fonts/sora-800.woff2') format('woff2'); }}
  @font-face {{ font-family: 'Manrope'; font-style: normal; font-weight: 400; font-display: swap; src: url('app/static/fonts/manrope-400.woff2') format('woff2'); }}
  @font-face {{ font-family: 'Manrope'; font-style: normal; font-weight: 500; font-display: swap; src: url('app/static/fonts/manrope-500.woff2') format('woff2'); }}
  @font-face {{ font-family: 'Manrope'; font-style: normal; font-weight: 600; font-display: swap; src: url('app/static/fonts/manrope-600.woff2') format('woff2'); }}

  #MainMenu, header, footer {{visibility: hidden;}}
  /* O bloco que carrega este CSS nao deve ocupar espaco nem gap no layout. */
  div[data-testid="stElementContainer"]:has(#crh-styles-marker),
  div[data-testid="stElementContainer"]:has(#crh-erro-marker),
  div[data-testid="stElementContainer"]:has(#crh-tema-marker) {{ display: none; }}

  .crh-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    margin-bottom: 28px;
  }}
  .crh-header .crh-mark {{ display: flex; align-items: center; gap: 12px; }}
  .crh-header .crh-mark .crh-icon {{ width: 44px; height: 44px; }}
  .crh-header .crh-wordmark {{
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    color: white;
  }}
  .crh-header .crh-wordmark .amber {{ color: {AMBAR}; }}
  .crh-header .crh-subtitle {{
    font-family: 'Manrope', sans-serif;
    font-weight: 500;
    font-size: 0.95rem;
    color: {CINZA_CLARO};
    margin: 0;
  }}

  /* Crachá de acesso: container com borda como card branco + aba ambar no topo.
     Padding e gap sao os valores reais medidos no Figma (pt-44 px-36 pb-40,
     gap-22 entre os blocos). Alvo via st.container(key="crh_card"), que o
     Streamlit expõe direto como classe "st-key-crh_card" no elemento. */
  .st-key-crh_card, .st-key-crh_card_codigo, .st-key-crh_card_largo {{
    position: relative;
    background: white !important;
    border-radius: 24px !important;
    border: none !important;
    box-shadow: 0px 20px 50px -10px rgba(0,0,0,0.35);
    padding: 44px 36px 40px 36px;
    margin: 14px auto 0 auto;
    gap: 22px;
  }}
  /* Larguras do Figma: login e senha 380px, codigo de acesso 400px, onboarding 460px. */
  .st-key-crh_card {{ max-width: 380px; }}
  .st-key-crh_card_codigo {{ max-width: 400px; gap: 20px; }}
  .st-key-crh_card_largo {{ max-width: 460px; padding: 40px 40px 36px 40px; }}
  .st-key-crh_card::before, .st-key-crh_card_codigo::before, .st-key-crh_card_largo::before {{
    content: "";
    position: absolute;
    top: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 64px;
    height: 16px;
    background: {AMBAR};
    border-radius: 8px;
  }}

  /* Titulo + subtitulo do card sao renderizados juntos num so bloco (ver
     theme.render_card_title) para ficarem colados entre si (gap-4 no Figma)
     e so terem o gap grande (22px) para o proximo elemento do card. */
  .crh-card-titleblock {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    text-align: center;
  }}
  .crh-card-title {{
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 1.35rem;
    color: {GRAFITE};
    margin: 0;
  }}
  .crh-card-subtitle {{
    font-family: 'Manrope', sans-serif;
    font-size: 13px;
    color: {GRAFITE_SECUNDARIO};
    margin: 0;
  }}

  /* O formulario nativo do Streamlit desenha uma moldura propria; no Figma os
     campos ficam soltos no cartao, com 22px entre cada bloco. */
  div[data-testid="stForm"] {{ border: none !important; padding: 0 !important; }}
  div[data-testid="stForm"] > div[data-testid="stVerticalBlock"] {{ gap: 22px; }}

  /* Campos no padrao "marfim" do Figma: rotulo 12px Medium, campo de 43px com
     borda de 1px e raio 10. Foco: anel ambar de 2px (Design System, "Foco visivel"). */
  .stTextInput label p {{
    font-family: 'Manrope', sans-serif;
    font-weight: 500;
    font-size: 12px;
    color: {GRAFITE};
  }}
  .stTextInput [data-testid="stTextInputRootElement"] {{
    background: {MARFIM};
    border: 1px solid {BORDA};
    border-radius: 10px;
    overflow: hidden;
  }}
  .stTextInput [data-testid="stTextInputRootElement"]:focus-within {{
    outline: 2px solid {AMBAR};
    outline-offset: 2px;
  }}
  .stTextInput [data-testid="stTextInputRootElement"] > div {{ background: transparent; }}
  .stTextInput input {{
    background: transparent;
    border: none;
    font-family: 'Manrope', sans-serif;
    font-size: 14px;
    color: {GRAFITE};
    padding: 12px 14px;
  }}
  /* "Press Enter to submit form" e o contador de caracteres: nao existem no Figma. */
  div[data-testid="InputInstructions"] {{ display: none; }}
  .stTextInput input::placeholder {{ color: {GRAFITE_SECUNDARIO}; opacity: 0.8; }}
  /* Botao de mostrar a senha: continua disponivel, no tom do campo. */
  .stTextInput [data-testid="stTextInputRootElement"] button {{ background: transparent; color: {GRAFITE_SECUNDARIO}; }}
  .stTextInput [data-testid="stTextInputRootElement"] button svg {{ fill: {GRAFITE_SECUNDARIO}; }}

  /* Botao primario ambar, texto grafite (igual ao Figma). O texto fica num
     elemento interno, que o Streamlit pinta de branco por padrao. */
  .stButton button[kind="primary"], .stFormSubmitButton button[kind="primaryFormSubmit"] {{
    background: {AMBAR};
    color: {GRAFITE};
    border: none;
    border-radius: 10px;
    padding: 0.7rem 0;
  }}
  .stButton button[kind="primary"] p, .stFormSubmitButton button[kind="primaryFormSubmit"] p {{
    color: {GRAFITE} !important;
    font-family: 'Manrope', sans-serif;
    font-weight: 600;
    font-size: 14px;
  }}
  .stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primaryFormSubmit"]:hover {{
    background: {AMBAR_ESCURO};
  }}
  /* Botão desligado: mais claro e sem o cursor de clique (a cor sozinha não basta, então também a opacidade). */
  .stButton button:disabled {{ opacity: 0.45; cursor: not-allowed; }}
  .stButton button:focus-visible, .stFormSubmitButton button:focus-visible {{
    outline: 2px solid {AMBAR};
    outline-offset: 2px;
  }}

  /* Links secundarios no estilo "Esqueci minha senha" / "Reenviar codigo":
     usa o botao nativo type="tertiary" do Streamlit (kind="tertiary" no DOM)
     em vez de tentar envolver um widget existente numa div customizada -
     cada st.html()/st.markdown() vira um no isolado no DOM, entao uma div
     aberta numa chamada nao chega a "abracar" um widget renderizado depois.
     Dentro de um formulario o tipo e "tertiaryFormSubmit". */
  [data-testid="stMain"] button[kind="tertiary"], [data-testid="stMain"] button[kind="tertiaryFormSubmit"] {{
    padding: 0 !important;
    min-height: 0 !important;
    background: transparent !important;
  }}
  [data-testid="stMain"] button[kind="tertiary"] p, [data-testid="stMain"] button[kind="tertiaryFormSubmit"] p {{
    color: {AMBAR_ESCURO} !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12px !important;
  }}
  [data-testid="stMain"] button[kind="tertiary"]:hover p, [data-testid="stMain"] button[kind="tertiaryFormSubmit"]:hover p {{ text-decoration: underline; }}
  /* "Esqueci minha senha" fica entre os campos e o botao Entrar no Figma, mas o
     botao Entrar vem primeiro no HTML: assim a tecla Enter envia o login. */
  .st-key-btn_esqueci, .st-key-btn_reenviar_otp {{ order: 1; }}
  .st-key-btn_entrar, .st-key-btn_validar {{ order: 2; }}
  .st-key-btn_reenviar_otp, .st-key-btn_sair_troca, .st-key-btn_voltar_login {{ display: flex; justify-content: center; width: 100% !important; }}
  .st-key-btn_reenviar_otp > div, .st-key-btn_sair_troca > div, .st-key-btn_voltar_login > div {{
    width: auto !important; display: flex; justify-content: center;
  }}

  /* Link do aviso abaixo do cartão de login (Figma 282:868). */
  .st-key-crh_link_aviso {{ margin-top: 18px; align-items: center; gap: 6px; }}
  .crh-link-aviso-rotulo {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 12px; color: {CINZA_CLARO}; }}
  .st-key-btn_link_aviso button p {{ color: {AMBAR} !important; }}

  .crh-otp-caption {{
    font-family: 'Manrope', sans-serif;
    font-size: 12px;
    color: {GRAFITE_SECUNDARIO};
    text-align: center;
    margin: 0;
  }}

  /* Alertas do protótipo (Alert/Erro 224:583, Aviso/Sessão expirada 224:619):
     ficam dentro do cartão, abaixo do título. Cor mais texto: a cor nunca é a
     única pista. */
  .crh-alerta {{
    display: flex; gap: 8px; align-items: flex-start;
    border-radius: 10px; padding: 10px 14px;
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13px; line-height: 1.4;
  }}
  .crh-alerta p {{ margin: 0; font: inherit; color: inherit; }}
  .crh-alerta.erro {{ background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.35); color: {ERRO}; }}
  .crh-alerta.sucesso {{ background: rgba(22,163,74,0.08); border: 1px solid rgba(22,163,74,0.35); color: {SUCESSO}; }}
  .crh-alerta.atencao {{ background: {AMBAR_BG}; border: 1px solid {AMBAR}; color: {GRAFITE}; }}
  .crh-aviso {{
    display: flex; gap: 10px; align-items: flex-start;
    background: {AMBAR_BG}; border: 1px solid {AMBAR}; border-radius: 10px; padding: 12px 14px;
  }}
  .crh-aviso .crh-aviso-icone {{
    font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {AMBAR_ESCURO}; line-height: 1.3;
  }}
  .crh-aviso .crh-aviso-titulo {{
    margin: 0 0 2px 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 13px; color: {GRAFITE};
  }}
  .crh-aviso .crh-aviso-texto {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 12px; line-height: 1.45; color: {GRAFITE_SECUNDARIO};
  }}

  /* Codigo de acesso: um unico campo desenhado como 6 caixas de 48x56 com 10px
     entre elas (Figma 224:228). Os algarismos usam largura fixa (tnum) para cair
     no meio de cada caixa. */
  .st-key-campo_codigo [data-testid="stTextInputRootElement"] {{
    background: transparent; border: none; border-radius: 10px; overflow: clip; width: 338px; height: 56px; max-width: 100%;
  }}
  /* O campo e mais largo que as 6 caixas; a moldura corta o excesso, e o anel de foco
     (2px ambar, Design System) contorna o conjunto das caixas. "overflow: clip" e nao
     "hidden": o hidden deixa o navegador rolar a moldura ate o cursor, que fica depois do
     ultimo digito. */
  .st-key-campo_codigo [data-testid="stTextInputRootElement"]:focus-within {{
    outline: 2px solid {AMBAR}; outline-offset: 2px;
  }}
  .st-key-campo_codigo input {{
    /* 6 passos de 58px + o recuo inicial: o campo precisa ser mais largo que as caixas
       (o ultimo passo leva 10px de espaco depois do ultimo digito); com largura menor o
       navegador rola o texto para acompanhar o cursor. */
    height: 56px; width: 366px; max-width: none; flex: 0 0 366px;
    padding-top: 0; padding-bottom: 0; padding-right: 0; text-indent: 0;
    font-family: 'Sora', sans-serif; font-weight: 800; font-size: 20px;
    font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;
    letter-spacing: 44.5px; padding-left: 17.25px;
    caret-color: {AMBAR_ESCURO};
    /* O SVG vai com "<" e ">" codificados: um "<" cru dentro do bloco de estilo
       faz o DOMPurify descartar o bloco inteiro (ver o comentario no topo). */
    background-image: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='58' height='56'%3E%3Crect x='0.75' y='0.75' width='46.5' height='54.5' rx='10' ry='10' fill='%23FAF9F6' stroke='%23F5A623' stroke-width='1.5'/%3E%3C/svg%3E");
    background-repeat: repeat-x; background-size: 58px 56px; background-position: 0 0;
  }}
  .st-key-campo_codigo input:focus-visible {{ outline: none; }}
  .st-key-campo_codigo label {{ display: none; }}
  .st-key-campo_codigo {{ display: flex; justify-content: center; }}

  /* Campo com erro (Figma 224:583): borda vermelha de 1,5px. */
  .crh-campo-erro [data-testid="stTextInputRootElement"] {{ border: 1.5px solid {ERRO} !important; }}

  /* Onboarding, boas-vindas do primeiro acesso (Figma 310:2477): progresso, resumo e trilha. */
  .crh-onb-topo {{ display: flex; align-items: flex-start; gap: 12px; justify-content: space-between; }}
  .crh-onb-topo {{ width: 100%; }}
  .crh-onb-topo .crh-card-titleblock {{ align-items: flex-start; text-align: left; flex: 1 1 auto; min-width: 0; }}
  .crh-onb-progresso {{
    background: {AMBAR_BG}; color: {AMBAR_ESCURO}; border-radius: 999px; padding: 5px 10px;
    font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 12px; white-space: nowrap; margin: 0; flex: none;
  }}
  .crh-onb-resumo {{
    background: {MARFIM}; border-radius: 8px; padding: 10px 12px; margin: 0;
    font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 11.5px; color: {GRAFITE_SECUNDARIO};
  }}
  .crh-trilha {{ display: flex; flex-direction: column; gap: 2px; }}
  .crh-trilha-item {{ display: flex; gap: 14px; align-items: stretch; }}
  .crh-trilha-ponto {{ width: 16px; display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; padding-top: 8px; }}
  .crh-trilha-ponto .p {{ width: 10px; height: 10px; border-radius: 999px; background: {AMBAR}; flex-shrink: 0; }}
  .crh-trilha-ponto .p.ok {{ background: {SUCESSO}; }}
  .crh-trilha-ponto .l {{ width: 2px; flex: 1 1 auto; background: {BORDA}; min-height: 20px; }}
  .crh-trilha-item:last-child .l {{ display: none; }}
  .crh-trilha-texto {{ display: flex; flex-direction: column; gap: 1px; padding: 8px 0; }}
  .crh-trilha-texto .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 14px; color: {GRAFITE}; }}
  .crh-trilha-texto .s {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-trilha-texto .s.ok {{ color: {SUCESSO}; }}
  .crh-trilha-texto .s.voce {{ color: {AMBAR_ESCURO}; }}
  /* Aviso de privacidade (Figma 285:874 e 285:1073). */
  .crh-aviso-pg {{ display: flex; flex-direction: column; gap: 20px; }}
  .crh-aviso-pg .cab .t {{ margin: 0; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 30px; color: {GRAFITE}; }}
  .crh-aviso-pg .cab .s {{ margin: 6px 0 10px 0; font-family: 'Manrope', sans-serif; font-size: 14.5px; line-height: 1.5; color: {GRAFITE_SECUNDARIO}; }}
  .crh-aviso-pg .selos {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .crh-aviso-pg .selo {{ border-radius: 999px; padding: 4px 10px; font-family: 'Manrope', sans-serif; font-size: 12px; font-weight: 500; }}
  .crh-aviso-pg .selo.a {{ background: {AMBAR_BG}; color: {AMBAR_ESCURO}; }}
  .crh-aviso-pg .selo.n {{ background: white; border: 1px solid {BORDA}; color: {GRAFITE}; }}
  .crh-aviso-pg .bloco {{ background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 22px 28px; display: flex; flex-direction: column; gap: 10px; }}
  .crh-aviso-pg .bloco.tab {{ padding: 0; overflow: hidden; gap: 0; }}
  .crh-aviso-pg .bloco.tab h2 {{ padding: 22px 28px 12px 28px; }}
  .crh-aviso-pg h2 {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 18px; color: {GRAFITE}; }}
  .crh-aviso-pg p, .crh-aviso-pg li {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13.5px; line-height: 1.55; color: {GRAFITE_SECUNDARIO}; }}
  .crh-aviso-pg strong {{ color: {GRAFITE}; font-weight: 600; }}
  .crh-aviso-pg ul, .crh-aviso-pg ol {{ margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 6px; }}
  .crh-aviso-pg table {{ width: 100%; border-collapse: collapse; }}
  .crh-aviso-pg th {{ background: {MARFIM}; text-align: left; padding: 10px 14px; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 12px; color: {GRAFITE_SECUNDARIO}; border-top: 1px solid {BORDA}; border-bottom: 1px solid {BORDA}; }}
  .crh-aviso-pg td {{ vertical-align: top; padding: 14px; font-family: 'Manrope', sans-serif; font-size: 12.5px; line-height: 1.5; color: {GRAFITE_SECUNDARIO}; border-bottom: 1px solid {BORDA}; }}
  .crh-aviso-pg td:first-child {{ color: {GRAFITE}; font-weight: 600; width: 24%; }}
  .crh-aviso-pg tr:last-child td {{ border-bottom: none; }}
  .crh-aviso-pg .destaque {{ background: {AMBAR_BG}; border-radius: 10px; padding: 12px 16px; font-weight: 600; color: {GRAFITE}; }}
  .crh-aviso-pg .campos {{ background: {MARFIM}; border: 1px solid {BORDA}; border-radius: 10px; padding: 10px 14px; display: grid; grid-template-columns: max-content 1fr; gap: 6px 24px; }}
  .crh-aviso-pg .campos .r {{ font-size: 12.5px; }}
  .crh-aviso-pg .campos .v {{ color: {GRAFITE}; font-weight: 600; }}
  .crh-onb-nota {{
    margin: 0; text-align: center; font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 11px; color: {GRAFITE_SECUNDARIO};
  }}
</style>
"""


# Tela de autenticação: fundo grafite, crachá centralizado (nós 28:27/31:6).
_AUTH_CSS = f"""
<style>
  .stApp {{ background: {GRAFITE}; }}
  .block-container {{
    max-width: 520px;
    padding-top: 4rem;
    padding-bottom: 3rem;
  }}
</style>
"""

# Aviso de privacidade sem login (Figma 285:874): faixa grafite com o logo e o botão Entrar,
# conteúdo de 880px sobre fundo marfim.
_AVISO_CSS = f"""
<style>
  .stApp {{ background: {MARFIM}; }}
  .block-container {{ max-width: 928px; padding: 0 24px 48px 24px !important; }}
  .st-key-aviso_faixa {{
    background: {GRAFITE}; width: 100vw !important; max-width: 100vw; margin: 0 0 32px calc(50% - 50vw) !important;
    padding: 14px max(24px, calc(50vw - 440px)); justify-content: space-between; align-items: center;
  }}
  .st-key-aviso_faixa .crh-side-logo {{ margin: 0; }}
  .st-key-aviso_faixa .crh-side-logo span {{ font-family: 'Sora', sans-serif; font-weight: 800; font-size: 22px; color: white; }}
  .st-key-aviso_faixa .crh-side-logo .amber {{ color: {AMBAR}; }}
  .st-key-aviso_faixa .crh-side-logo img {{ width: 30px; height: 30px; }}
  .st-key-aviso_faixa .crh-side-logo {{ display: flex; align-items: center; gap: 8px; }}
  .st-key-aviso_faixa button[kind="primary"] {{ padding: 0.45rem 1rem; width: auto; }}
  .st-key-btn_aviso_voltar button {{ background: white !important; border: 1px solid {BORDA}; border-radius: 10px; padding: 0.55rem 1rem !important; }}
  .st-key-btn_aviso_voltar button p {{ color: {GRAFITE} !important; font-size: 13px !important; }}
</style>
"""

# Área logada: sidebar grafite de 240px + conteúdo em fundo branco (nó 62:38
# "Início"). Valores de padding/gap/raio/fonte são os do Figma.
_APP_CSS = f"""
<style>
  .stApp {{ background: white; }}
  .block-container {{
    max-width: none;
    padding: 40px 48px !important;
  }}
  .block-container > div[data-testid="stVerticalBlock"] {{ gap: 24px; }}

  section[data-testid="stSidebar"] {{
    background: {GRAFITE};
    width: 240px !important;
    min-width: 240px !important;
    max-width: 240px !important;
  }}
  div[data-testid="stSidebarHeader"], div[data-testid="stSidebarCollapseButton"] {{ display: none; }}
  div[data-testid="stSidebarContent"], div[data-testid="stSidebarUserContent"] {{ padding: 0 !important; }}
  /* O Streamlit reserva calha de scrollbar nas duas bordas (10px cada), o que
     deslocaria o conteudo do padding de 16px do Figma. */
  div[data-testid="stSidebarContent"] {{ scrollbar-gutter: auto; }}
  div[data-testid="stSidebarUserContent"] {{ padding: 28px 16px !important; }}
  div[data-testid="stSidebarUserContent"] div[data-testid="stVerticalBlock"] {{ gap: 4px; }}

  .crh-side-logo {{ display: flex; align-items: center; gap: 10.4px; margin-bottom: 20px; }}
  .crh-side-logo img {{ width: 36.4px; height: 36.4px; }}
  .crh-side-logo span {{
    font-family: 'Sora', sans-serif; font-weight: 800; font-size: 26px; color: white;
  }}
  .crh-side-logo .amber {{ color: {AMBAR}; }}

  .crh-nav-ativo {{
    background: {AMBAR};
    border-radius: 8px;
    padding: 10px 12px;
    font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px;
    color: {GRAFITE};
  }}
  div[class*="st-key-nav_"] button {{
    width: 100%;
    justify-content: flex-start;
    padding: 10px 12px !important;
    border-radius: 8px;
    min-height: 0;
    text-align: left;
  }}
  div[class*="st-key-nav_"] button > div {{ justify-content: flex-start; }}
  div[class*="st-key-nav_"] button p {{
    white-space: nowrap; line-height: normal; text-align: left;
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 14px;
    color: {CINZA_CLARO};
  }}
  div[class*="st-key-nav_"] button:hover {{ background: rgba(255,255,255,0.06); }}
  div[class*="st-key-nav_"] button:hover p {{ color: white; }}

  .crh-topbar {{ display: flex; justify-content: flex-end; align-items: center; gap: 16px; }}
  .crh-topbar .crh-bell {{ width: 40px; height: 40px; }}
  .crh-chip {{
    display: flex; align-items: center; gap: 8px;
    background: white; border: 1px solid {BORDA}; border-radius: 10px;
    padding: 6px 12px 6px 8px;
  }}
  .crh-chip .crh-avatar {{
    width: 28px; height: 28px; border-radius: 999px; background: {GRAFITE};
    display: flex; align-items: center; justify-content: center;
    font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 11px; color: {AMBAR};
  }}
  .crh-chip .crh-nome {{
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13px; color: {GRAFITE};
  }}

  .crh-hero {{
    background: {GRAFITE}; border-radius: 16px; padding: 28px 32px;
    display: flex; flex-direction: column; gap: 8px;
  }}
  .crh-hero .crh-hero-titulo {{ display: flex; align-items: center; gap: 12px; }}
  .crh-hero .crh-hero-barra {{ width: 4px; height: 30px; border-radius: 2px; background: {AMBAR}; }}
  .crh-hero .crh-hero-titulo p {{
    margin: 0; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 26px; color: white;
  }}
  .crh-hero .crh-hero-sub {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 14px; color: {CINZA_CLARO};
  }}

  .crh-linha {{ display: flex; gap: 16px; align-items: flex-start; }}
  .crh-painel {{
    background: white; border: 1px solid {BORDA}; border-radius: 14px;
    box-shadow: 0px 1px 3px 0px rgba(22,24,29,0.06);
  }}
  .crh-stat {{ flex: 1 0 0; min-width: 0; padding: 18px 20px; display: flex; flex-direction: column; gap: 2px; }}
  .crh-stat .crh-stat-rotulo {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 12px; color: {GRAFITE_SECUNDARIO};
  }}
  .crh-stat .crh-stat-valor {{
    margin: 0; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 24px; color: {GRAFITE};
  }}
  .crh-stat .crh-stat-valor.positivo {{ color: {SUCESSO}; }}
  .crh-stat .crh-stat-valor.negativo {{ color: {ERRO}; }}

  .crh-bloco {{ padding: 22px 24px; display: flex; flex-direction: column; gap: 14px; }}
  .crh-bloco.flex {{ flex: 1 0 0; min-width: 0; }}
  .crh-bloco.fixo {{ width: 340px; flex-shrink: 0; }}
  .crh-bloco-titulo {{
    margin: 0; font-family: 'Sora', sans-serif; font-weight: 600; font-size: 16px; color: {GRAFITE};
  }}
  .crh-comunicado {{ border-bottom: 1px solid {BORDA}; padding: 10px 0; display: flex; flex-direction: column; gap: 2px; }}
  .crh-comunicado .crh-com-titulo {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13.5px; color: {GRAFITE};
  }}
  .crh-meta {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 12px; color: {GRAFITE_SECUNDARIO};
  }}
  .crh-aniv {{ display: flex; align-items: center; gap: 10px; }}
  .crh-aniv .crh-aniv-icone {{
    width: 28px; height: 28px; border-radius: 999px; background: {AMBAR_BG};
    display: flex; align-items: center; justify-content: center; font-size: 13px;
  }}
  .crh-aniv .crh-aniv-nome {{
    flex: 1 0 0; min-width: 0; margin: 0;
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13px; color: {GRAFITE};
  }}

  .crh-faq {{ padding: 18px 24px; display: flex; align-items: center; gap: 14px; }}
  .crh-faq > div {{ flex: 1 0 0; min-width: 0; display: flex; flex-direction: column; gap: 2px; }}
  .crh-faq .crh-faq-titulo {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE};
  }}
  .crh-faq .crh-faq-link {{
    margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 13px; color: {AMBAR_ESCURO};
  }}

  /* Onboarding na área logada ("Meu onboarding" 309:1048 e card do Início 309:1446): cartões
     com a borda e o raio dos blocos do Figma, selos de status e barra de progresso. */
  .st-key-onb_voce, .st-key-onb_rh, .st-key-onb_gestor, .st-key-onb_inicio, .st-key-onb_pendencias {{
    background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 22px; gap: 14px;
  }}
  .st-key-onb_voce button[kind="primary"], .st-key-onb_inicio button[kind="primary"] {{ width: auto; padding: 0.55rem 1.1rem; }}
  .crh-stat .crh-stat-valor.verde {{ color: {SUCESSO}; }}
  .crh-stat .crh-stat-valor.ambar {{ color: {AMBAR_ESCURO}; }}
  .crh-stat .crh-stat-valor.azul {{ color: #2663D9; }}
  .crh-card-h {{ display: flex; flex-direction: column; gap: 4px; }}
  .crh-card-h .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 17px; color: {GRAFITE}; }}
  .crh-card-h .s {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-linha-onb {{
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    border: 1px solid {BORDA}; border-radius: 12px; padding: 12px 14px;
  }}
  .crh-linha-onb .txt {{ display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
  .crh-linha-onb .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .crh-linha-onb .d {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 400; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-selo {{
    flex-shrink: 0; border-radius: 999px; padding: 4px 10px; white-space: nowrap;
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 12px;
  }}
  .crh-selo.ok {{ background: #DCFCE7; color: {SUCESSO}; }}
  .crh-selo.amb {{ background: {AMBAR_BG}; color: {AMBAR_ESCURO}; }}
  .crh-selo.neu {{ background: {MARFIM}; color: {GRAFITE_SECUNDARIO}; }}
  .crh-selo.azul {{ background: #E0EBFF; color: #2663D9; }}
  .crh-barra {{ display: flex; flex-direction: column; gap: 6px; }}
  .crh-barra .topo {{
    display: flex; justify-content: space-between;
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13px; color: {GRAFITE};
  }}
  .crh-barra .topo span:last-child {{ color: {GRAFITE_SECUNDARIO}; }}
  .crh-barra .trilho {{ height: 8px; border-radius: 4px; background: {BORDA}; overflow: hidden; }}
  .crh-barra .preenchido {{ height: 100%; border-radius: 4px; background: {AMBAR}; }}
  .crh-selo.err {{ background: #FEE2E2; color: {ERRO}; }}

  /* Menu da conta (Figma 198:158): o chip do nome abre um popover com o perfil, Configurações e Sair. */
  .st-key-crh_topbar {{ justify-content: flex-end; align-items: center; gap: 16px; }}
  .st-key-crh_topbar [data-testid="stPopover"] button {{
    background: white; border: 1px solid {BORDA}; border-radius: 10px; padding: 6px 12px 6px 8px; min-height: 0;
  }}
  .st-key-crh_topbar [data-testid="stPopover"] button p {{
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13px; color: {GRAFITE};
  }}
  [data-testid="stPopoverBody"] {{
    background: white !important; border: 1px solid {BORDA}; border-radius: 16px;
    box-shadow: 0px 12px 32px -8px rgba(22,24,29,0.25); min-width: 300px;
  }}
  [data-testid="stPopoverBody"] button[kind="tertiary"] {{ padding: 0 !important; min-height: 0 !important; background: transparent !important; }}
  .crh-menu-conta {{ display: flex; align-items: center; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid {BORDA}; }}
  .crh-menu-conta .crh-avatar-g {{
    width: 40px; height: 40px; border-radius: 999px; background: {GRAFITE}; color: {AMBAR}; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px;
  }}
  .crh-menu-conta .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 15px; color: {GRAFITE}; }}
  .crh-menu-conta .s {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 12.5px; color: {GRAFITE_SECUNDARIO}; }}
  .st-key-btn_menu_config button p {{ color: {GRAFITE} !important; font-size: 15px !important; font-weight: 500 !important; }}
  .st-key-btn_menu_sair button p {{ color: {ERRO} !important; font-size: 15px !important; font-weight: 500 !important; }}
  .st-key-menu_tema_linha {{ justify-content: space-between; padding: 6px 0; border-top: 1px solid {BORDA}; border-bottom: 1px solid {BORDA}; }}
  .crh-menu-tema {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 15px; color: {GRAFITE}; }}
  .st-key-menu_tema [data-testid="stButtonGroup"] {{ background: {MARFIM}; border: 1px solid {BORDA}; border-radius: 8px; padding: 3px; }}
  .st-key-menu_tema button {{ border: none !important; background: transparent; border-radius: 6px !important; padding: 2px 10px; min-height: 0; }}
  .st-key-menu_tema button p {{ font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .st-key-menu_tema button[aria-checked="true"] {{ background: {AMBAR} !important; }}
  .st-key-menu_tema button[aria-checked="true"] p {{ color: {GRAFITE} !important; }}
  .crh-menu-sub {{ margin: -6px 0 0 0; font-family: 'Manrope', sans-serif; font-size: 12.5px; color: {GRAFITE_SECUNDARIO}; }}

  /* Título de página sem faixa grafite (Configurações 286:878, aviso logado 285:1073). */
  .crh-titulo-pagina {{ display: flex; flex-direction: column; gap: 6px; }}
  .crh-titulo-pagina .t {{ margin: 0; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 30px; color: {GRAFITE}; }}
  .crh-titulo-pagina .s {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 15px; color: {GRAFITE_SECUNDARIO}; }}

  /* Abas de Configurações: controle segmentado no estilo do Figma (fundo marfim, ativa em âmbar). */
  .st-key-cfg_abas [data-testid="stButtonGroup"] {{ background: {MARFIM}; border: 1px solid {BORDA}; border-radius: 12px; padding: 4px; width: fit-content; }}
  .st-key-cfg_abas button {{ border: none !important; background: transparent; border-radius: 10px !important; padding: 8px 18px; }}
  .st-key-cfg_abas button p {{ font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 14px; color: {GRAFITE_SECUNDARIO}; }}
  .st-key-cfg_abas button[aria-checked="true"] {{ background: {AMBAR} !important; }}
  .st-key-cfg_abas button[aria-checked="true"] p {{ color: {GRAFITE}; font-weight: 600; }}

  /* Cartões de Configurações → Privacidade e de Documentos. */
  div[class*="st-key-cfg_card_"], .st-key-doc_lista {{
    background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 24px; gap: 14px;
  }}
  div[class*="st-key-cfg_card_"] button[kind="primary"], .st-key-doc_topo button[kind="primary"] {{ width: auto; padding: 0.6rem 1.1rem; }}
  div[class*="st-key-cfg_card_"] button[kind="secondary"] {{ border: 1px solid {BORDA}; border-radius: 10px; padding: 0.6rem 1.1rem; background: white; }}
  div[class*="st-key-cfg_card_"] button[kind="secondary"] p {{ font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .crh-cfg-titulo {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 18px; color: {GRAFITE}; }}
  .crh-cfg-texto {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 14px; line-height: 1.45; color: {GRAFITE_SECUNDARIO}; }}
  .crh-cfg-nota {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 12.5px; line-height: 1.45; color: {GRAFITE_SECUNDARIO}; }}
  .crh-cfg-selos {{ display: flex; align-items: center; gap: 12px; }}
  .crh-campos {{ background: {MARFIM}; border: 1px solid {BORDA}; border-radius: 10px; padding: 12px 16px; display: grid; grid-template-columns: max-content 1fr; gap: 6px 28px; }}
  .crh-campos .r {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-campos .v {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  /* Botões liga/desliga com o texto à esquerda e o botão à direita (Figma 286:878). */
  .st-key-pref_aniversario, .st-key-pref_mural {{ width: 100% !important; }}
  .st-key-pref_aniversario label, .st-key-pref_mural label {{ flex-direction: row-reverse; justify-content: space-between; width: 100%; }}
  .st-key-pref_aniversario [data-testid="stWidgetLabel"] p, .st-key-pref_mural [data-testid="stWidgetLabel"] p {{
    font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE};
  }}

  /* Documentos (Figma 41:26): linha do tempo com um ponto colorido por documento. */
  .st-key-doc_topo {{ justify-content: space-between; align-items: center; }}
  .crh-doc-lista {{ display: flex; flex-direction: column; gap: 4px; }}
  .crh-doc-item {{ display: flex; gap: 14px; align-items: stretch; }}
  .crh-doc-item .ponto {{ width: 10px; display: flex; flex-direction: column; align-items: center; gap: 4px; padding-top: 4px; }}
  .crh-doc-item .ponto .p {{ width: 10px; height: 10px; border-radius: 999px; background: {CINZA_CLARO}; flex-shrink: 0; }}
  .crh-doc-item .ponto .p.ok {{ background: {SUCESSO}; }}
  .crh-doc-item .ponto .p.amb, .crh-doc-item .ponto .p.azul {{ background: {AMBAR}; }}
  .crh-doc-item .ponto .p.err {{ background: {ERRO}; }}
  .crh-doc-item .ponto .l {{ width: 2px; flex: 1 1 auto; background: {BORDA}; }}
  .crh-doc-item:last-child .ponto .l {{ display: none; }}
  .crh-doc-item .crh-linha-onb {{ flex: 1 1 auto; margin-bottom: 6px; }}

  /* Documentos pendentes (Figma 309:1249): tabela, pendências em fundo creme. */
  .st-key-doc_pendentes {{ background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 0; gap: 0; overflow: hidden; }}
  .st-key-doc_pendentes div[class*="st-key-doc_lin"] {{ border-bottom: 1px solid {BORDA}; padding: 12px 18px; gap: 0; align-items: center; }}
  .st-key-doc_pendentes div[class*="st-key-doc_linf_"] {{ background: #FFFBEB; }}
  .st-key-doc_pendentes .st-key-doc_cab {{ background: {MARFIM}; border-bottom: 1px solid {BORDA}; padding: 10px 18px; }}
  .crh-doc-cab {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-doc-cel .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 14px; color: {GRAFITE}; }}
  .crh-doc-cel .d {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-doc-prazo {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 14px; color: {GRAFITE}; }}
  .st-key-doc_pendentes button[kind="tertiary"] p {{ font-size: 13.5px !important; }}

  /* Conferência de documentos do RH (Figma 418:1108): mesma tabela, ações em texto colorido. */
  .st-key-rh_tabela {{ background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 0; gap: 0; overflow: hidden; }}
  .st-key-rh_tabela div[class*="st-key-rh_lin"] {{ border-bottom: 1px solid {BORDA}; padding: 12px 18px; gap: 0; }}
  .st-key-rh_tabela div[class*="st-key-rh_linf_"] {{ background: #FFFBEB; }}
  .st-key-rh_tabela .st-key-rh_cab {{ background: {MARFIM}; border-bottom: 1px solid {BORDA}; padding: 10px 18px; }}
  .st-key-rh_tabela button[kind="tertiary"] p {{ font-size: 13.5px !important; }}
  .st-key-rh_tabela div[class*="st-key-rh_recusar_"] button p {{ color: {ERRO} !important; }}
  .st-key-rh_tabela div[class*="st-key-rh_arquivar_"] button p {{ color: {GRAFITE} !important; }}
  .st-key-rh_tabela div[class*="st-key-rh_abrir_"] button p {{ color: {GRAFITE} !important; font-weight: 500 !important; }}
  .st-key-rh_barra {{ gap: 12px; }}
  .st-key-rh_barra button[kind="secondary"] {{ background: white; border: 1px solid {BORDA}; border-radius: 10px; padding: 0.55rem 1.1rem; }}
  .st-key-rh_barra button[kind="secondary"] p {{ font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .st-key-rh_barra .stSelectbox > div > div {{ background: white !important; border: 1px solid {BORDA} !important; border-radius: 10px; }}
  .st-key-rh_barra .stSelectbox div:has(> input[role="combobox"]), .st-key-rh_barra .stSelectbox div:has(> div > input[role="combobox"]) {{ background: transparent !important; }}
  .st-key-rh_barra .stSelectbox div, .st-key-rh_barra .stSelectbox input {{ color: {GRAFITE} !important; }}
  .crh-campos-direita .v {{ text-align: right; }}

  /* Meu Perfil (Figma 202:175): cartões com campos em duas colunas, pendências e organograma. */
  div[class*="st-key-perfil_card_"] {{ background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 24px 28px; gap: 14px; }}
  .st-key-perfil_card_pendencias {{ border-color: {AMBAR} !important; }}
  div[class*="st-key-perfil_card_"] button[kind="primary"] {{ width: auto; padding: 0.4rem 0.9rem; }}
  div[class*="st-key-perfil_card_"] button[kind="primary"] p {{ font-size: 13px !important; }}
  .crh-campos-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px 40px; }}
  .crh-campos-grid .r {{ margin: 0 0 2px 0; font-family: 'Manrope', sans-serif; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-campos-grid .v {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 15px; color: {GRAFITE}; }}
  .crh-pf-titulo {{ display: flex; align-items: center; gap: 10px; }}
  .crh-pf-contador {{ width: 24px; height: 24px; border-radius: 999px; background: {AMBAR_BG}; color: {AMBAR_ESCURO}; font-family: 'Manrope', sans-serif; font-size: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center; }}
  .crh-pf-lista {{ display: flex; flex-direction: column; }}
  .crh-pf-item {{ display: flex; gap: 12px; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid {BORDA}; }}
  .crh-pf-item:last-child {{ border-bottom: none; }}
  .crh-pf-item .p {{ width: 6px; height: 6px; border-radius: 999px; background: {AMBAR}; margin-top: 8px; flex-shrink: 0; }}
  .crh-pf-item .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 14px; color: {GRAFITE}; }}
  .crh-pf-item .d {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-org {{ display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }}
  .crh-org-linha {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .crh-org-seta {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-org-pessoa {{ display: flex; gap: 10px; align-items: center; background: {MARFIM}; border: 1px solid transparent; border-radius: 10px; padding: 10px 14px 10px 12px; }}
  .crh-org-pessoa.voce {{ background: {AMBAR_BG}; border-color: {AMBAR}; }}
  .crh-org-pessoa .a {{ width: 30px; height: 30px; border-radius: 999px; background: {GRAFITE}; color: {AMBAR}; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 11px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
  .crh-org-pessoa .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13.5px; color: {GRAFITE}; }}
  .crh-org-pessoa .d {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 11.5px; color: {GRAFITE_SECUNDARIO}; }}

  /* Ponto (Figma 39:18): caixas do dia, saldo, aviso e espelho da semana. */
  .st-key-ponto_card_hoje, .st-key-ponto_card_saldo {{ background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 22px 24px; gap: 14px; }}
  div[class*="st-key-ponto_box_"] {{ border-radius: 12px; padding: 18px 12px; gap: 6px; align-items: center; text-align: center; min-height: 108px; }}
  div[class*="st-key-ponto_box_feito_"] {{ background: #DCFCE7; }}
  div[class*="st-key-ponto_box_proximo_"], div[class*="st-key-ponto_box_futuro_"] {{ background: {MARFIM}; border: 1px solid {BORDA}; }}
  div[class*="st-key-ponto_box_"] .stButton {{ display: flex; justify-content: center; }}
  div[class*="st-key-ponto_box_"] button[kind="primary"] {{ width: auto; padding: 0.35rem 0.9rem; }}
  div[class*="st-key-ponto_box_"] button[kind="primary"] p {{ font-size: 12.5px !important; }}
  div[class*="st-key-ponto_box_feito_"] button[kind="tertiary"] p {{ color: {SUCESSO} !important; font-weight: 500 !important; }}
  .crh-ponto-rotulo {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13px; color: {GRAFITE}; }}
  div[class*="st-key-ponto_box_feito_"] .crh-ponto-rotulo, div[class*="st-key-ponto_box_feito_"] .crh-ponto-hora {{ color: {SUCESSO}; }}
  .crh-ponto-hora {{ margin: 0; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 22px; color: {GRAFITE}; }}
  .crh-ponto-saldo {{ margin: 0; font-family: 'Sora', sans-serif; font-weight: 800; font-size: 24px; color: {GRAFITE}; }}
  .crh-ponto-saldo.positivo {{ color: {SUCESSO}; }}
  .crh-ponto-saldo.negativo {{ color: {ERRO}; }}
  .crh-ponto-aviso {{ margin: 0; background: {AMBAR_BG}; border-radius: 8px; padding: 10px 14px; font-family: 'Manrope', sans-serif; font-size: 12.5px; color: #B45309; }}
  .st-key-ponto_topo_espelho button[kind="secondary"] {{ background: white; border: 1px solid {BORDA}; border-radius: 10px; padding: 0.55rem 1.1rem; }}
  .st-key-ponto_topo_espelho button[kind="secondary"] p {{ font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .st-key-ponto_tabela {{ background: white; border: 1px solid {BORDA}; border-radius: 16px; padding: 0; gap: 0; overflow: hidden; }}
  .st-key-ponto_tabela div[class*="st-key-ponto_lin"] {{ border-bottom: 1px solid {BORDA}; padding: 10px 18px; gap: 0; }}
  .st-key-ponto_tabela div[class*="st-key-ponto_lina_"] {{ background: #EEF4FF; }}
  .st-key-ponto_tabela .st-key-ponto_cab {{ background: {MARFIM}; border-bottom: 1px solid {BORDA}; padding: 10px 18px; }}
  .st-key-ponto_tabela button[kind="tertiary"] p {{ font-size: 13px !important; }}
  .crh-ponto-marca {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 13.5px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-ponto-trab {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .crh-ponto-status {{ margin: 0; font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 12.5px; letter-spacing: 0.02em; }}
  .crh-ponto-status.ok {{ color: {SUCESSO}; }}
  .crh-ponto-status.amb {{ color: {AMBAR_ESCURO}; }}
  .crh-ponto-status.err {{ color: {ERRO}; }}
  .crh-ponto-status.azul {{ color: #2663D9; }}

  /* Férias (Figma 40:22): cartões no topo e histórico com linha do tempo. */
  .st-key-ferias_topo {{ gap: 16px; }}
  .st-key-ferias_topo .crh-painel.crh-stat {{ display: inline-flex; width: calc(50% - 8px); vertical-align: top; }}
  .st-key-ferias_topo .stHtml {{ flex: 1 1 auto; }}
  .st-key-ferias_topo .stHtml > div {{ display: flex; gap: 16px; }}
  .st-key-ferias_topo button[kind="secondary"] {{ background: white; border: 1px solid {BORDA}; border-radius: 10px; padding: 0.7rem 1.4rem; }}
  .st-key-ferias_topo button[kind="secondary"] p {{ font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .st-key-ferias_topo button[kind="primary"] {{ width: auto; padding: 0.7rem 1.4rem; }}
  .st-key-ferias_historico {{ gap: 8px; }}
  div[class*="st-key-ferias_lin_"] {{ background: white; border: 1px solid {BORDA}; border-radius: 12px; padding: 12px 16px; gap: 14px; }}
  div[class*="st-key-ferias_lin_"] button[kind="tertiary"] p {{ color: {ERRO} !important; font-size: 13px !important; }}
  .crh-fe-item {{ display: flex; gap: 14px; align-items: center; }}
  .crh-fe-item .p {{ width: 10px; height: 10px; border-radius: 999px; background: {CINZA_CLARO}; flex-shrink: 0; }}
  .crh-fe-item .p.ok {{ background: {SUCESSO}; }}
  .crh-fe-item .p.amb {{ background: {AMBAR}; }}
  .crh-fe-item .p.err {{ background: {ERRO}; }}
  .crh-fe-item .t {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 14px; color: {GRAFITE}; }}
  .crh-fe-item .d {{ margin: 0; font-family: 'Manrope', sans-serif; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}

  /* Grupo do menu lateral por perfil (Design System 314:786): rótulo em caixa alta. */
  .crh-nav-grupo {{ margin: 14px 0 2px 12px; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 11px; letter-spacing: 0.06em; color: #737A85; text-transform: uppercase; }}

  /* Modais (st.dialog) claros como no Figma (286:1062, 224:2379, 309:1591): o tema base do app é
     escuro por causa da tela Entrar, então cada parte do modal ganha a cor do protótipo. */
  [data-testid="stDialog"] > div {{ background: white !important; border-radius: 20px !important; color: {GRAFITE}; }}
  [data-testid="stDialog"] h2, [data-testid="stDialog"] h2 span {{ font-family: 'Sora', sans-serif !important; font-weight: 800 !important; color: {GRAFITE} !important; }}
  [data-testid="stDialog"] button[aria-label="Close"] svg {{ fill: {GRAFITE_SECUNDARIO}; color: {GRAFITE_SECUNDARIO}; }}
  [data-testid="stDialog"] [data-testid="stWidgetLabel"] p, [data-testid="stDialog"] label p {{
    font-family: 'Manrope', sans-serif; font-weight: 500; font-size: 13.5px; color: {GRAFITE} !important;
  }}
  [data-testid="stDialog"] [data-testid="stCaptionContainer"] p, [data-testid="stDialog"] .stRadio [data-testid="stCaptionContainer"] {{ color: {GRAFITE_SECUNDARIO} !important; }}
  [data-testid="stDialog"] [data-baseweb="select"] > div, [data-testid="stDialog"] [data-baseweb="input"], [data-testid="stDialog"] [data-baseweb="textarea"],
  [data-testid="stDialog"] [data-testid="stDateInputField"], [data-testid="stDialog"] [data-testid="stTextInputRootElement"] {{
    background: {MARFIM} !important; border: 1px solid {BORDA} !important; border-radius: 10px !important; color: {GRAFITE} !important;
  }}
  [data-testid="stDialog"] .stSelectbox div:has(> input[role="combobox"]), [data-testid="stDialog"] .stSelectbox div:has(> div > input[role="combobox"]) {{ background: transparent !important; }}
  [data-testid="stDialog"] .stSelectbox [data-testid="stSelectboxVirtualDropdown"], [data-testid="stDialog"] .stSelectbox > div > div {{ background: {MARFIM} !important; color: {GRAFITE} !important; border-radius: 10px; }}
  [data-testid="stDialog"] [data-testid="stTextAreaRootElement"], [data-testid="stDialog"] [data-testid="stNumberInputContainer"] {{
    background: {MARFIM} !important; border: 1px solid {BORDA} !important; border-radius: 10px !important;
  }}
  [data-testid="stDialog"] [data-testid="stTextAreaRootElement"] > div, [data-testid="stDialog"] [data-testid="stNumberInputContainer"] > div {{ background: transparent !important; }}
  [data-testid="stDialog"] .stSelectbox > div > div {{ border: 1px solid {BORDA} !important; }}
  [data-testid="stDialog"] .stDateInput span {{ color: {GRAFITE} !important; }}
  [data-testid="stDialog"] input:disabled {{ -webkit-text-fill-color: {GRAFITE_SECUNDARIO}; color: {GRAFITE_SECUNDARIO} !important; opacity: 1; cursor: default; }}
  [data-testid="stDialog"] [data-testid="stTimeInputTimeDisplay"] {{ background: {MARFIM} !important; border: 1px solid {BORDA}; border-radius: 10px; color: {GRAFITE} !important; }}
  [data-testid="stDialog"] [data-testid="stTimeInputTimeDisplay"] * {{ color: {GRAFITE} !important; }}
  /* Bolinha do radio não marcado: anel cinza e miolo branco (o tema base escuro a pinta de preto). */
  [data-testid="stDialog"] [role="radiogroup"] label:not(:has(input:checked)) div:has(> div:empty) {{ background: #C9C7C1 !important; }}
  [data-testid="stDialog"] [role="radiogroup"] label:not(:has(input:checked)) div:empty {{ background: white !important; }}
  [data-testid="stDialog"] input, [data-testid="stDialog"] textarea {{ -webkit-text-fill-color: {GRAFITE}; }}
  [data-testid="stDialog"] input::placeholder, [data-testid="stDialog"] textarea::placeholder {{ color: {GRAFITE_SECUNDARIO}; -webkit-text-fill-color: {GRAFITE_SECUNDARIO}; opacity: 0.8; }}
  [data-testid="stDialog"] input, [data-testid="stDialog"] textarea, [data-testid="stDialog"] [data-baseweb="select"] div {{ color: {GRAFITE} !important; background: transparent !important; }}
  [data-testid="stDialog"] button[kind="secondary"] {{ background: white; border: 1px solid {BORDA}; border-radius: 10px; padding: 0.6rem 1.1rem; }}
  [data-testid="stDialog"] button[kind="secondary"] p {{ color: {GRAFITE} !important; font-family: 'Manrope', sans-serif; font-weight: 600; }}
  [data-testid="stDialog"] button[kind="primary"] {{ padding: 0.6rem 1.2rem; width: auto; }}
  [data-testid="stDialog"] [data-testid="stTooltipIcon"] svg {{ stroke: {GRAFITE_SECUNDARIO}; }}
  .crh-incluso {{ background: {MARFIM}; border-radius: 12px; padding: 14px 16px; }}
  .crh-incluso .t {{ margin: 0 0 6px 0; font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 14px; color: {GRAFITE}; }}
  .crh-incluso ul {{ margin: 0; padding-left: 18px; font-family: 'Manrope', sans-serif; font-size: 13.5px; line-height: 1.75; color: {GRAFITE_SECUNDARIO}; }}
  .crh-incluso .n {{ margin: 6px 0 0 0; font-family: 'Manrope', sans-serif; font-size: 12px; color: {GRAFITE_SECUNDARIO}; }}
  .crh-nota-verde {{ background: #DCFCE7; color: {SUCESSO}; border-radius: 10px; padding: 12px 14px; margin: 0; font-family: 'Manrope', sans-serif; font-size: 13px; line-height: 1.45; }}
  .crh-nota-ambar {{ background: {AMBAR_BG}; color: {GRAFITE}; border-radius: 10px; padding: 12px 14px; margin: 0; font-family: 'Manrope', sans-serif; font-size: 13.5px; }}
</style>
"""


# ---------------------------------------------------------------------------
# Modo escuro (tarefa 63 da change concluir-frontend-streamlit). Tokens do Design System
# "Modo escuro e componentes" (Figma 294:622): card, modal e campo claro #FFFFFF -> #22252C;
# fundo e campo #FAF9F6 -> #16181D; borda #E4E3DF -> #33363E; texto #16181D -> #F2F2F0;
# secundário #4B5563 -> #A3A3AA; cinza neutro #F3F3F1 -> #2B2E36. Botão âmbar, selos pastel e
# sidebar não mudam. É uma camada por cima do CSS claro: só troca cores.
# ---------------------------------------------------------------------------
ESC_FUNDO = "#16181D"
ESC_CARTAO = "#22252C"
ESC_BORDA = "#33363E"
ESC_TEXTO = "#F2F2F0"
ESC_TEXTO_2 = "#A3A3AA"
ESC_NEUTRO = "#2B2E36"
ESC_AMBAR_SUAVE = "#2A2417"

_ESCURO_CSS = f"""
<style>
  /* crh-tema-escuro */
  .stApp {{ background: {ESC_FUNDO} !important; }}
  /* Faixa do título: no escuro ela some no fundo (Figma 108:870). */
  .crh-hero {{ background: transparent; padding-left: 0; padding-right: 0; }}
  .crh-painel, .st-key-onb_voce, .st-key-onb_rh, .st-key-onb_gestor, .st-key-onb_inicio, .st-key-onb_pendencias,
  div[class*="st-key-cfg_card_"], .st-key-doc_lista, .st-key-doc_pendentes, .crh-aviso-pg .bloco {{
    background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; box-shadow: none;
  }}
  .crh-stat .crh-stat-rotulo, .crh-meta, .crh-card-h .s, .crh-linha-onb .d, .crh-titulo-pagina .s, .crh-cfg-texto,
  .crh-cfg-nota, .crh-menu-sub, .crh-menu-conta .s, .crh-campos .r, .crh-doc-cab, .crh-doc-cel .d, .crh-trilha-texto .s,
  .crh-barra .topo span:last-child, .crh-incluso ul, .crh-incluso .n, .crh-aviso-pg p, .crh-aviso-pg li, .crh-aviso-pg td,
  .crh-aviso-pg th, .crh-aviso-pg .cab .s, .crh-onb-resumo {{ color: {ESC_TEXTO_2} !important; }}
  .crh-stat .crh-stat-valor:not(.verde):not(.ambar):not(.azul):not(.positivo):not(.negativo), .crh-bloco-titulo,
  .crh-comunicado .crh-com-titulo, .crh-aniv .crh-aniv-nome, .crh-faq .crh-faq-titulo, .crh-card-h .t, .crh-linha-onb .t,
  .crh-barra .topo, .crh-titulo-pagina .t, .crh-cfg-titulo, .crh-campos .v, .crh-doc-cel .t, .crh-doc-prazo,
  .crh-menu-conta .t, .crh-trilha-texto .t, .crh-incluso .t, .crh-aviso-pg h2, .crh-aviso-pg strong,
  .crh-aviso-pg .cab .t, .crh-aviso-pg td:first-child, .crh-aviso-pg .campos .v, .crh-chip .crh-nome {{ color: {ESC_TEXTO} !important; }}
  .crh-comunicado, .crh-linha-onb, .crh-aviso-pg td, .crh-aviso-pg th {{ border-color: {ESC_BORDA} !important; }}
  .crh-linha-onb {{ background: transparent; }}
  .crh-doc-item .crh-linha-onb {{ background: {ESC_CARTAO}; }}
  .crh-campos, .crh-incluso, .crh-onb-resumo, .crh-aviso-pg .campos, .crh-aviso-pg th, .st-key-doc_pendentes .st-key-doc_cab {{
    background: {ESC_FUNDO} !important; border-color: {ESC_BORDA} !important;
  }}
  .crh-barra .trilho, .crh-doc-item .ponto .l, .crh-trilha-ponto .l {{ background: {ESC_BORDA}; }}
  .crh-selo.neu {{ background: {ESC_NEUTRO}; color: {ESC_TEXTO_2}; }}
  .crh-nota-ambar, .crh-aviso-pg .destaque {{ background: {ESC_AMBAR_SUAVE} !important; color: {ESC_TEXTO} !important; }}
  .st-key-doc_pendentes div[class*="st-key-doc_linf_"] {{ background: {ESC_AMBAR_SUAVE}; }}
  .st-key-doc_pendentes div[class*="st-key-doc_lin"] {{ border-color: {ESC_BORDA}; }}
  .st-key-rh_tabela {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  div[class*="st-key-perfil_card_"] {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA}; }}
  .st-key-ponto_card_hoje, .st-key-ponto_card_saldo, .st-key-ponto_tabela {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  div[class*="st-key-ferias_lin_"] {{ background: {ESC_CARTAO}; border-color: {ESC_BORDA}; }}
  .crh-fe-item .t {{ color: {ESC_TEXTO}; }}
  .crh-fe-item .d {{ color: {ESC_TEXTO_2}; }}
  .st-key-ferias_topo button[kind="secondary"] {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  .st-key-ferias_topo button[kind="secondary"] p {{ color: {ESC_TEXTO} !important; }}
  div[class*="st-key-ponto_box_proximo_"], div[class*="st-key-ponto_box_futuro_"] {{ background: {ESC_FUNDO}; border-color: {ESC_BORDA}; }}
  div[class*="st-key-ponto_box_feito_"] {{ background: #12301F; }}
  div[class*="st-key-ponto_box_feito_"] .crh-ponto-rotulo, div[class*="st-key-ponto_box_feito_"] .crh-ponto-hora, div[class*="st-key-ponto_box_feito_"] button[kind="tertiary"] p {{ color: #4ADE80 !important; }}
  .crh-ponto-rotulo, .crh-ponto-hora, .crh-ponto-trab, .crh-ponto-saldo:not(.positivo):not(.negativo) {{ color: {ESC_TEXTO}; }}
  .crh-ponto-marca {{ color: {ESC_TEXTO_2}; }}
  .crh-ponto-aviso {{ background: {ESC_AMBAR_SUAVE}; color: {AMBAR}; }}
  .st-key-ponto_tabela div[class*="st-key-ponto_lin"] {{ border-color: {ESC_BORDA}; }}
  .st-key-ponto_tabela div[class*="st-key-ponto_lina_"] {{ background: #1B2436; }}
  .st-key-ponto_tabela .st-key-ponto_cab {{ background: {ESC_FUNDO}; border-color: {ESC_BORDA}; }}
  .st-key-ponto_topo_espelho button[kind="secondary"] {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  .st-key-ponto_topo_espelho button[kind="secondary"] p {{ color: {ESC_TEXTO} !important; }}
  .st-key-perfil_card_pendencias {{ border-color: {AMBAR} !important; }}
  .crh-campos-grid .r, .crh-pf-item .d, .crh-org-seta, .crh-org-pessoa .d {{ color: {ESC_TEXTO_2} !important; }}
  .crh-campos-grid .v, .crh-pf-item .t, .crh-org-pessoa .t {{ color: {ESC_TEXTO} !important; }}
  .crh-pf-item {{ border-color: {ESC_BORDA}; }}
  .crh-org-pessoa {{ background: {ESC_FUNDO}; }}
  .crh-org-pessoa.voce {{ background: {ESC_AMBAR_SUAVE}; border-color: {AMBAR}; }}
  .crh-pf-contador {{ background: {ESC_AMBAR_SUAVE}; color: {AMBAR}; }}
  .st-key-rh_tabela div[class*="st-key-rh_lin"] {{ border-color: {ESC_BORDA}; }}
  .st-key-rh_tabela div[class*="st-key-rh_linf_"] {{ background: {ESC_AMBAR_SUAVE}; }}
  .st-key-rh_tabela .st-key-rh_cab {{ background: {ESC_FUNDO}; border-color: {ESC_BORDA}; }}
  .st-key-rh_tabela div[class*="st-key-rh_arquivar_"] button p, .st-key-rh_tabela div[class*="st-key-rh_abrir_"] button p {{ color: {ESC_TEXTO} !important; }}
  .st-key-rh_barra button[kind="secondary"], .st-key-rh_barra .stSelectbox > div > div {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  .st-key-rh_barra button[kind="secondary"] p, .st-key-rh_barra .stSelectbox div, .st-key-rh_barra .stSelectbox input {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] [data-testid="stTextAreaRootElement"], [data-testid="stDialog"] [data-testid="stNumberInputContainer"] {{ background: {ESC_FUNDO} !important; border-color: {ESC_BORDA} !important; }}
  .crh-aviso-pg .selo.n {{ background: {ESC_CARTAO}; border-color: {ESC_BORDA}; color: {ESC_TEXTO}; }}
  .crh-aviso-pg .selo.a {{ background: {ESC_AMBAR_SUAVE}; color: {AMBAR}; }}

  /* Barra superior, menu da conta e abas (o sino escuro é outro SVG, ver render_topbar). */
  .st-key-crh_topbar [data-testid="stPopover"] button {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  .st-key-crh_topbar [data-testid="stPopover"] button p {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stPopoverBody"] {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  .crh-menu-conta {{ border-color: {ESC_BORDA}; }}
  .st-key-btn_menu_config button p, .crh-menu-tema {{ color: {ESC_TEXTO} !important; }}
  .st-key-menu_tema_linha {{ border-color: {ESC_BORDA}; }}
  .st-key-cfg_abas [data-testid="stButtonGroup"], .st-key-menu_tema [data-testid="stButtonGroup"] {{ background: {ESC_FUNDO}; border-color: {ESC_BORDA}; }}
  .st-key-cfg_abas button p, .st-key-menu_tema button p {{ color: {ESC_TEXTO_2}; }}
  .st-key-pref_aniversario [data-testid="stWidgetLabel"] p, .st-key-pref_mural [data-testid="stWidgetLabel"] p {{ color: {ESC_TEXTO} !important; }}
  div[class*="st-key-cfg_card_"] button[kind="secondary"], .st-key-btn_aviso_voltar button {{ background: {ESC_CARTAO} !important; border-color: {ESC_BORDA} !important; }}
  div[class*="st-key-cfg_card_"] button[kind="secondary"] p, .st-key-btn_aviso_voltar button p {{ color: {ESC_TEXTO} !important; }}

  /* Modais. */
  [data-testid="stDialog"] > div {{ background: {ESC_CARTAO} !important; color: {ESC_TEXTO}; }}
  [data-testid="stDialog"] h2, [data-testid="stDialog"] h2 span {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] [data-testid="stWidgetLabel"] p, [data-testid="stDialog"] label p {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] [data-testid="stCaptionContainer"] p {{ color: {ESC_TEXTO_2} !important; }}
  [data-testid="stDialog"] [data-baseweb="select"] > div, [data-testid="stDialog"] [data-baseweb="input"], [data-testid="stDialog"] [data-baseweb="textarea"],
  [data-testid="stDialog"] [data-testid="stDateInputField"], [data-testid="stDialog"] [data-testid="stTextInputRootElement"],
  [data-testid="stDialog"] .stSelectbox > div > div {{ background: {ESC_FUNDO} !important; border-color: {ESC_BORDA} !important; color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] input, [data-testid="stDialog"] textarea, [data-testid="stDialog"] [data-baseweb="select"] div {{ color: {ESC_TEXTO} !important; -webkit-text-fill-color: {ESC_TEXTO}; }}
  [data-testid="stDialog"] input::placeholder, [data-testid="stDialog"] textarea::placeholder {{ color: {ESC_TEXTO_2}; -webkit-text-fill-color: {ESC_TEXTO_2}; }}
  [data-testid="stDialog"] .stSelectbox > div > div {{ border-color: {ESC_BORDA} !important; }}
  [data-testid="stDialog"] .stDateInput span {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] input:disabled {{ -webkit-text-fill-color: {ESC_TEXTO_2}; color: {ESC_TEXTO_2} !important; }}
  [data-testid="stDialog"] [data-testid="stTimeInputTimeDisplay"] {{ background: {ESC_FUNDO} !important; border-color: {ESC_BORDA}; }}
  [data-testid="stDialog"] [data-testid="stTimeInputTimeDisplay"] * {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] [role="radiogroup"] label:not(:has(input:checked)) div:has(> div:empty) {{ background: {ESC_TEXTO_2} !important; }}
  [data-testid="stDialog"] [role="radiogroup"] label:not(:has(input:checked)) div:empty {{ background: {ESC_CARTAO} !important; }}
  [data-testid="stDialog"] button[kind="secondary"] {{ background: {ESC_CARTAO}; border-color: {ESC_BORDA}; }}
  [data-testid="stDialog"] button[kind="secondary"] p {{ color: {ESC_TEXTO} !important; }}
  [data-testid="stDialog"] button[aria-label="Close"] svg {{ fill: {ESC_TEXTO_2}; color: {ESC_TEXTO_2}; }}
</style>
"""

# Aviso sem login no escuro: fundo grafite em vez de marfim (Figma 292:1001).
_AVISO_ESCURO_CSS = f"""
<style>
  .stApp {{ background: {ESC_FUNDO} !important; }}
  .st-key-aviso_faixa {{ border-bottom: 1px solid {ESC_BORDA}; }}
</style>
"""

TEMAS = ("claro", "escuro")
_COOKIE_TEMA = "crh_tema"


def tema_atual() -> str:
    """"claro" ou "escuro": a escolha desta sessão; senão a guardada no navegador (cookie de
    preferência, sem dado pessoal); senão claro."""
    tema = st.session_state.get("tema")
    if tema in TEMAS:
        return tema
    try:
        tema = st.context.cookies.get(_COOKIE_TEMA)
    except Exception:  # fora de um navegador (AppTest)
        tema = None
    return tema if tema in TEMAS else "claro"


def _guardar_tema_no_navegador(tema: str) -> None:
    """Grava a preferência num cookie de 1 ano, para o próximo acesso abrir no mesmo tema. O valor
    é sempre "claro" ou "escuro" (nunca texto do usuário)."""
    valor = "escuro" if tema == "escuro" else "claro"
    st.html(
        '<div id="crh-tema-marker" style="display:none"></div>'
        f"<script>document.cookie='{_COOKIE_TEMA}={valor}; path=/; max-age=31536000; SameSite=Lax';</script>",
        unsafe_allow_javascript=True,
    )


def _trocar_tema() -> None:
    """Callback do seletor do menu da conta."""
    escolha = st.session_state.get("menu_tema")
    st.session_state.tema = "escuro" if escolha == "Escuro" else "claro"
    st.session_state.tema_gravar = True


def inject_base_styles(area: str = "auth") -> None:
    """Injeta o CSS comum mais o da área ("auth" = login/OTP, "app" = telas logadas)."""
    # Dois problemas empilhados, achados inspecionando o bundle JS do
    # Streamlit (static/static/js/Html.BWKIiOvA.js) e o DOM ao vivo via
    # Chrome DevTools Protocol - nao por tentativa e erro:
    #
    # 1. streamlit/elements/html.py tem um caso especial (_html_only_style_
    #    tags): quando o body enviado e SO uma tag <style> (sem mais nada),
    #    o Streamlit desvia isso para um "event container" separado em vez
    #    do container normal da pagina - nesse caminho o elemento nem chega
    #    a aparecer no DOM principal. Um marcador antes do <style> evita
    #    esse desvio.
    # 2. Mesmo indo pelo container normal, st.html() sempre sanitiza com
    #    DOMPurify. Com unsafe_allow_javascript=False (o padrao), o config
    #    do DOMPurify NAO inclui 'style' em ADD_TAGS - a tag e removida na
    #    sanitizacao. So com unsafe_allow_javascript=True o Streamlit usa
    #    ADD_TAGS: ['script','style'], preservando o <style>. Nao
    #    precisamos de JS de verdade aqui, so desse efeito colateral da
    #    flag para o CSS sobreviver.
    area_css = {"app": _APP_CSS, "aviso": _AVISO_CSS}.get(area, _AUTH_CSS)
    # O tema escuro vale para a área logada e para o aviso; a tela Entrar já é grafite.
    if tema_atual() == "escuro" and area in ("app", "aviso"):
        area_css += _ESCURO_CSS + (_AVISO_ESCURO_CSS if area == "aviso" else "")
    st.html(
        '<div id="crh-styles-marker" style="display:none"></div>' + _BASE_CSS + area_css,
        unsafe_allow_javascript=True,
    )
    if st.session_state.pop("tema_gravar", False):
        _guardar_tema_no_navegador(tema_atual())


def render_header(subtitle: str) -> None:
    st.html(
        f"""
        <div class="crh-header">
          <div class="crh-mark">
            <img src="{_LOGO_ICON_DATA_URI}" alt="" class="crh-icon" />
            <span class="crh-wordmark">conecta<span class="amber">RH</span></span>
          </div>
          <p class="crh-subtitle">{html.escape(subtitle)}</p>
        </div>
        """
    )


def render_card_title(title: str, subtitle: str) -> None:
    """Título + subtítulo do card, num único bloco (ver .crh-card-titleblock) -
    ambos precisam nascer no mesmo st.html() para ficarem colados entre si
    (gap-4 do Figma) e não herdar o gap-22 grande usado entre os elementos
    do card. O texto é escapado: o subtítulo pode trazer dado digitado pelo
    usuário (ex.: o e-mail no passo do código de acesso)."""
    st.html(
        f"""
        <div class="crh-card-titleblock">
          <p class="crh-card-title">{html.escape(title)}</p>
          <p class="crh-card-subtitle">{html.escape(subtitle)}</p>
        </div>
        """
    )


def render_sidebar_logo() -> None:
    st.html(
        f"""
        <div class="crh-side-logo">
          <img src="{_LOGO_ICON_DATA_URI}" alt="" />
          <span>conecta<span class="amber">RH</span></span>
        </div>
        """
    )


def render_nav_ativo(rotulo: str) -> None:
    st.html(f'<div class="crh-nav-ativo">{html.escape(rotulo)}</div>')


_PERFIS = {"RH": "RH", "ADMIN": "Admin", "GESTOR": "Gestor", "COLABORADOR": "Colaborador"}


def iniciais(nome: str) -> str:
    partes = [p for p in nome.split() if p[:1].isalpha()]
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper() if partes else ""


def render_topbar(nome: str) -> None:
    """Sino e chip do nome (Figma 62:38). O chip abre o menu da conta (Figma 198:158): perfil,
    "Configurações" e "Sair da conta". As ações só deixam um pedido em `st.session_state`
    (`ir_configuracoes`, `sair_da_conta`), tratado pelo app.py."""
    usuario = st.session_state.get("usuario") or {}
    perfil = _PERFIS.get(str(usuario.get("perfil", "")).upper(), str(usuario.get("perfil", "")).title())
    with st.container(horizontal=True, key="crh_topbar"):
        sino = _BELL_ESCURO_DATA_URI if tema_atual() == "escuro" else _BELL_DATA_URI
        st.html(f'<img src="{sino}" alt="Notificações" class="crh-bell" style="width:40px;height:40px" />', width="content")
        with st.popover(nome, key="menu_conta"):
            st.html(
                f"""
                <div class="crh-menu-conta">
                  <div class="crh-avatar-g">{html.escape(iniciais(nome))}</div>
                  <div><p class="t">{html.escape(nome)}</p><p class="s">Perfil: {html.escape(perfil)}</p></div>
                </div>
                """
            )
            if st.button("Configurações", type="tertiary", key="btn_menu_config"):
                st.session_state.ir_configuracoes = True
                st.rerun()
            st.html('<p class="crh-menu-sub">Senha, sessões e notificações</p>')
            with st.container(horizontal=True, vertical_alignment="center", key="menu_tema_linha"):
                st.html('<p class="crh-menu-tema">Tema</p>', width="content")
                st.segmented_control(
                    "Tema",
                    ["Claro", "Escuro"],
                    default="Escuro" if tema_atual() == "escuro" else "Claro",
                    required=True,
                    key="menu_tema",
                    on_change=_trocar_tema,
                    label_visibility="collapsed",
                )
            if st.button("Sair da conta", type="tertiary", key="btn_menu_sair"):
                st.session_state.sair_da_conta = True
                st.rerun()


def render_titulo_pagina(titulo: str, subtitulo: str) -> None:
    """Título grande sem a faixa grafite (Configurações 286:878)."""
    st.html(
        f'<div class="crh-titulo-pagina"><p class="t">{html.escape(titulo)}</p>'
        f'<p class="s">{html.escape(subtitulo)}</p></div>'
    )


def render_logo_faixa() -> None:
    st.html(
        f'<div class="crh-side-logo"><img src="{_LOGO_ICON_DATA_URI}" alt="" />'
        '<span>conecta<span class="amber">RH</span></span></div>',
        width="content",
    )


def html_aviso(aviso: dict, em_html, subtitulo_extra: str = "") -> str:
    """O aviso de privacidade inteiro (Figma 285:874), a partir de aviso_privacidade.carregar().

    `em_html` converte cada trecho de Markdown em HTML seguro (escapado, só com negrito)."""
    selos = "".join(
        f'<span class="selo {"a" if i == 0 else "n"}">{html.escape(s)}</span>' for i, s in enumerate(aviso["selos"])
    )
    tabela = aviso["tabela"]
    cab = "".join(f"<th>{html.escape(c)}</th>" for c in tabela["cabecalho"])
    linhas = "".join("<tr>" + "".join(f"<td>{em_html(c)}</td>" for c in l) + "</tr>" for l in tabela["linhas"])
    partes = [
        '<div class="crh-aviso-pg">',
        f'<div class="cab"><p class="t">{html.escape(aviso["titulo"].replace(" do ConectaRH", ""))}</p>'
        f'<p class="s">{em_html(aviso["intro"])}{html.escape(subtitulo_extra)}</p><div class="selos">{selos}</div></div>',
    ]
    for secao in aviso["secoes"]:
        if secao["titulo"].startswith("Quais dados"):
            partes.append(
                f'<div class="bloco tab"><h2>{html.escape(secao["titulo"])}</h2>'
                f"<table><thead><tr>{cab}</tr></thead><tbody>{linhas}</tbody></table></div>"
            )
            if aviso["destaque"]:
                partes.append(f'<p class="destaque">{em_html(aviso["destaque"]).replace("<strong>", "").replace("</strong>", "")}</p>')
            continue
        corpo = []
        for tipo, conteudo in secao["blocos"]:
            if tipo == "p":
                corpo.append(f"<p>{em_html(conteudo)}</p>")
            elif tipo in ("ul", "ol"):
                corpo.append(f"<{tipo}>" + "".join(f"<li>{em_html(i)}</li>" for i in conteudo) + f"</{tipo}>")
            elif tipo == "campos":
                corpo.append(
                    '<div class="campos">'
                    + "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{em_html(v)}</p>' for r, v in conteudo)
                    + "</div>"
                )
        partes.append(f'<div class="bloco"><h2>{html.escape(secao["titulo"])}</h2>{"".join(corpo)}</div>')
    partes.append("</div>")
    return "".join(partes)


def render_lista_documentos(linhas: list[dict]) -> None:
    """Lista com linha do tempo (Figma 41:26). Cada linha: {titulo, detalhe, badge, tipo}."""
    itens = "".join(
        f'<div class="crh-doc-item"><div class="ponto"><span class="p {l["tipo"]}"></span><span class="l"></span></div>'
        f'{html_linha_onboarding(l["titulo"], l.get("detalhe"), l["badge"], l["tipo"])}</div>'
        for l in linhas
    )
    st.html(f'<div class="crh-doc-lista">{itens}</div>')


# ---------------------------------------------------------------------------
# Alertas, aviso de sessão e campo com erro (fluxo de entrada, Figma F01)
# ---------------------------------------------------------------------------
def alerta(slot, tipo: str, mensagem: str) -> None:
    """Alerta dentro do cartão, abaixo do título (Figma 224:583).

    `slot` é um st.empty() reservado logo abaixo do título; o texto é escapado
    porque pode vir da API. `tipo`: "erro", "sucesso" ou "atencao"."""
    slot.html(f'<div class="crh-alerta {tipo}" role="alert"><p>{html.escape(mensagem)}</p></div>')


def aviso_cartao(slot, titulo: str, texto: str) -> None:
    """Aviso âmbar com título e texto (Figma 224:619, "Sua sessão terminou")."""
    slot.html(
        f"""
        <div class="crh-aviso" role="status">
          <span class="crh-aviso-icone" aria-hidden="true">!</span>
          <div>
            <p class="crh-aviso-titulo">{html.escape(titulo)}</p>
            <p class="crh-aviso-texto">{html.escape(texto)}</p>
          </div>
        </div>
        """
    )


def marcar_campo_erro(chave: str) -> None:
    """Borda vermelha de 1,5px no campo cuja `key` é `chave` (Figma 224:583).

    `chave` é sempre uma constante do código, nunca texto do usuário."""
    st.html(
        '<div id="crh-erro-marker" style="display:none"></div>'
        f'<style>.st-key-{chave} [data-testid="stTextInputRootElement"] {{ border: 1.5px solid {ERRO} !important; }}</style>',
        unsafe_allow_javascript=True,
    )


def render_onboarding_topo(titulo: str, subtitulo: str, progresso: str) -> None:
    st.html(
        f"""
        <div class="crh-onb-topo">
          <div class="crh-card-titleblock">
            <p class="crh-card-title">{html.escape(titulo)}</p>
            <p class="crh-card-subtitle">{html.escape(subtitulo)}</p>
          </div>
          <p class="crh-onb-progresso">{html.escape(progresso)}</p>
        </div>
        """
    )


def render_onboarding_resumo(texto: str) -> None:
    st.html(f'<p class="crh-onb-resumo">{html.escape(texto)}</p>')


def render_trilha(itens: list[dict]) -> None:
    """Trilha de etapas do onboarding. Cada item: {titulo, detalhe, concluido} e, opcional, tom ("ok" ou "voce")."""
    linhas = "".join(
        f'<div class="crh-trilha-item">'
        f'<div class="crh-trilha-ponto"><span class="p{" ok" if i["concluido"] else ""}"></span><span class="l"></span></div>'
        f'<div class="crh-trilha-texto"><p class="t">{html.escape(i["titulo"])}</p>'
        f'<p class="s{" " + i["tom"] if i.get("tom") else (" ok" if i["concluido"] else "")}">{html.escape(i["detalhe"])}</p></div></div>'
        for i in itens
    )
    st.html(f'<div class="crh-trilha">{linhas}</div>')


def render_nota(texto: str) -> None:
    st.html(f'<p class="crh-onb-nota">{html.escape(texto)}</p>')


# ---------------------------------------------------------------------------
# Área logada: faixa de título, indicadores, cartões e linhas do onboarding
# ---------------------------------------------------------------------------
def render_hero(titulo: str, subtitulo: str) -> None:
    """Faixa grafite com a régua âmbar (Figma 62:38, 309:1048). Texto escapado."""
    st.html(
        f"""
        <div class="crh-hero">
          <div class="crh-hero-titulo"><div class="crh-hero-barra"></div><p>{html.escape(titulo)}</p></div>
          <p class="crh-hero-sub">{html.escape(subtitulo)}</p>
        </div>
        """
    )


def render_indicadores(indicadores: list[tuple[str, str, str]]) -> None:
    """Quatro cartões de número. Cada item: (rótulo, valor, classe de cor: "", "verde", "ambar" ou "azul")."""
    st.html(
        '<div class="crh-linha">'
        + "".join(
            f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">{html.escape(r)}</p>'
            f'<p class="crh-stat-valor {cls}">{html.escape(v)}</p></div>'
            for r, v, cls in indicadores
        )
        + "</div>"
    )


def render_titulo_cartao(titulo: str, subtitulo: str | None = None) -> None:
    sub = f'<p class="s">{html.escape(subtitulo)}</p>' if subtitulo else ""
    st.html(f'<div class="crh-card-h"><p class="t">{html.escape(titulo)}</p>{sub}</div>')


def html_linha_onboarding(titulo: str, detalhe: str | None, selo: str, tipo: str) -> str:
    """Uma linha com título, detalhe opcional e selo de status. `tipo`: ok, amb, neu ou azul."""
    d = f'<p class="d">{html.escape(detalhe)}</p>' if detalhe else ""
    return (
        f'<div class="crh-linha-onb"><div class="txt"><p class="t">{html.escape(titulo)}</p>{d}</div>'
        f'<span class="crh-selo {tipo if tipo in ("ok", "amb", "neu", "azul", "err") else "neu"}">{html.escape(selo)}</span></div>'
    )


def render_linhas_onboarding(linhas: list[dict]) -> None:
    """Linhas {titulo, detalhe, badge, tipo} empilhadas com 10px entre elas."""
    corpo = "".join(html_linha_onboarding(l["titulo"], l.get("detalhe"), l["badge"], l["tipo"]) for l in linhas)
    st.html(f'<div style="display:flex;flex-direction:column;gap:10px">{corpo}</div>')


def render_barra_progresso(rotulo: str, percentual: int) -> None:
    pct = max(0, min(100, int(percentual)))
    st.html(
        f'<div class="crh-barra"><div class="topo"><span>{html.escape(rotulo)}</span><span>{pct}%</span></div>'
        f'<div class="trilho"><div class="preenchido" style="width:{pct}%"></div></div></div>'
    )

