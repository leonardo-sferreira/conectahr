"""
Tema visual do ConectaRH — extraído do protótipo Figma real (arquivo
"ConectaRH — Protótipo", fph1M5tB4rA4gqfIysSmkn, nós 28:27 e 31:6).

Streamlit não permite estilização pixel-perfect nativa, então usamos CSS
injetado via st.html() (não st.markdown(unsafe_allow_html=True) — este último
sanitiza e remove tags <style>/<link> com DOMPurify) para reproduzir os
tokens de design (cor, tipografia, o "crachá de acesso") o mais fiel
possível. Qualquer nova tela deve importar e reutilizar isto em vez de
redefinir estilo do zero.
"""

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

_ASSETS_DIR = Path(__file__).parent / "assets"
_LOGO_ICON_SVG = (_ASSETS_DIR / "logo-icon.svg").read_text(encoding="utf-8")

_BASE_CSS = f"""
<style>
  /* st.html() sanitiza com DOMPurify: permite <style>, mas remove tags
     <link> (usadas antes aqui para o Google Fonts - eram descartadas
     silenciosamente, o texto sumia e a fonte caia no padrao do sistema).
     @import dentro do proprio <style> sobrevive por ser so texto/CSS. */
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;800&family=Manrope:wght@400;500;600&display=swap');

  #MainMenu, header, footer {{visibility: hidden;}}

  .stApp {{
    background: {GRAFITE};
  }}

  .block-container {{
    max-width: 460px;
    padding-top: 4rem;
    padding-bottom: 3rem;
  }}

  .crh-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    margin-bottom: 28px;
  }}
  .crh-header .crh-mark {{ display: flex; align-items: center; gap: 12px; }}
  .crh-header .crh-mark svg {{ width: 44px; height: 44px; }}
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

  /* "Crachá de acesso": container com borda como card branco + aba ambar no topo.
     Padding e gap sao os valores reais medidos no Figma (pt-44 px-36 pb-40,
     gap-22 entre os blocos) - a versao anterior usava um padding bem menor
     (12/8/20px), o que deixava tudo espremido perto da borda do card. */
  div[data-testid="stVerticalBlockBorderWrapper"]:has(div.crh-card-marker) {{
    position: relative;
    background: white;
    border-radius: 24px !important;
    border: none !important;
    box-shadow: 0px 20px 50px -10px rgba(0,0,0,0.35);
    padding: 44px 36px 40px 36px;
    margin-top: 14px;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"]:has(div.crh-card-marker) > div[data-testid="stVerticalBlock"] {{
    gap: 22px;
  }}
  /* O marcador invisivel nao deve contar como um "bloco" no gap acima. */
  .crh-card-marker {{
    display: none;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"]:has(div.crh-card-marker)::before {{
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


def inject_base_styles() -> None:
    # st.markdown(unsafe_allow_html=True) sanitiza e remove tags <style>/<link>
    # por seguranca (mantendo so o texto de dentro visivel na pagina - foi
    # exatamente o bug visual que isso causou). st.html() nao sanitiza: e a
    # API certa do Streamlit para HTML/CSS de pagina que o proprio dev escreveu.
    st.html(_BASE_CSS)


def render_header(subtitle: str) -> None:
    st.html(
        f"""
        <div class="crh-header">
          <div class="crh-mark">
            {_LOGO_ICON_SVG}
            <span class="crh-wordmark">conecta<span class="amber">RH</span></span>
          </div>
          <p class="crh-subtitle">{subtitle}</p>
        </div>
        """
    )


def card_marker() -> None:
    """Marcador invisível — permite o CSS acima (:has(.crh-card-marker)) mirar só
    o container que envolve o crachá de acesso, sem afetar outros st.container()
    que o app venha a usar nas próximas telas."""
    st.html('<div class="crh-card-marker"></div>')


def render_card_title(title: str, subtitle: str) -> None:
    """Título + subtítulo do card, num único bloco (ver .crh-card-titleblock) -
    ambos precisam nascer no mesmo st.html() para ficarem colados entre si
    (gap-4 do Figma) e não herdar o gap-22 grande usado entre os elementos
    do card."""
    st.html(
        f"""
        <div class="crh-card-titleblock">
          <p class="crh-card-title">{title}</p>
          <p class="crh-card-subtitle">{subtitle}</p>
        </div>
        """
    )
