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
_BELL_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode((_ASSETS_DIR / "bell.svg").read_bytes()).decode("ascii")

_BASE_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;800&family=Manrope:wght@400;500;600&display=swap');

  #MainMenu, header, footer {{visibility: hidden;}}
  /* O bloco que carrega este CSS nao deve ocupar espaco nem gap no layout. */
  div[data-testid="stElementContainer"]:has(#crh-styles-marker) {{ display: none; }}

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
  .st-key-crh_card {{
    position: relative;
    background: white !important;
    border-radius: 24px !important;
    border: none !important;
    box-shadow: 0px 20px 50px -10px rgba(0,0,0,0.35);
    padding: 44px 36px 40px 36px;
    margin-top: 14px;
    gap: 22px;
  }}
  .st-key-crh_card::before {{
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
    font-size: 0.82rem;
    color: {GRAFITE_SECUNDARIO};
    margin: 0;
  }}

  /* Campos de texto no padrao "marfim" do protótipo */
  .stTextInput label p {{
    font-family: 'Manrope', sans-serif;
    font-weight: 500;
    font-size: 0.78rem;
    color: {GRAFITE};
  }}
  .stTextInput input {{
    background: {MARFIM};
    border: 1px solid {BORDA};
    border-radius: 10px;
    font-family: 'Manrope', sans-serif;
    color: {GRAFITE};
  }}

  /* Botao primario ambar, texto grafite (igual ao Figma) */
  .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {{
    background: {AMBAR};
    color: {GRAFITE};
    border: none;
    border-radius: 10px;
    font-family: 'Manrope', sans-serif;
    font-weight: 600;
    padding: 0.6rem 0;
  }}
  .stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {{
    background: {AMBAR_ESCURO};
    color: white;
  }}

  /* Links secundarios no estilo "Esqueci minha senha" / "Reenviar codigo":
     usa o botao nativo type="tertiary" do Streamlit (kind="tertiary" no DOM)
     em vez de tentar envolver um widget existente numa div customizada -
     cada st.html()/st.markdown() vira um no isolado no DOM, entao uma div
     aberta numa chamada nao chega a "abracar" um widget renderizado depois. */
  button[kind="tertiary"] {{
    color: {AMBAR_ESCURO} !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
  }}

  .crh-otp-caption {{
    font-family: 'Manrope', sans-serif;
    font-size: 0.78rem;
    color: {GRAFITE_SECUNDARIO};
    text-align: center;
  }}
</style>
"""


# Tela de autenticação: fundo grafite, crachá centralizado (nós 28:27/31:6).
_AUTH_CSS = f"""
<style>
  .stApp {{ background: {GRAFITE}; }}
  .block-container {{
    max-width: 460px;
    padding-top: 4rem;
    padding-bottom: 3rem;
  }}
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
</style>
"""


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
    area_css = _APP_CSS if area == "app" else _AUTH_CSS
    st.html(
        '<div id="crh-styles-marker" style="display:none"></div>' + _BASE_CSS + area_css,
        unsafe_allow_javascript=True,
    )


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


def render_topbar(nome: str) -> None:
    partes = nome.split()
    iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper() if partes else ""
    st.html(
        f"""
        <div class="crh-topbar">
          <img src="{_BELL_DATA_URI}" alt="Notificações" class="crh-bell" />
          <div class="crh-chip">
            <div class="crh-avatar">{html.escape(iniciais)}</div>
            <span class="crh-nome">{html.escape(nome)}</span>
          </div>
        </div>
        """
    )
