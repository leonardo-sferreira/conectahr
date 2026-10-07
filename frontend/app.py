"""
ConectaRH — ponto de entrada do frontend Streamlit.

Navegação com st.navigation/st.Page (design.md do change
implementar-frontend-streamlit): sem token só a página "Entrar" existe; com
token, as páginas da área logada. O menu nativo fica oculto (position="hidden")
e a sidebar é desenhada aqui, fiel ao protótipo Figma (nó 62:38): logo, item
ativo em âmbar e os demais itens em cinza.

A lista de itens por perfil é só conveniência de navegação — a autorização
real continua sendo do backend.
"""

import streamlit as st

from pagina_entrar import pagina_entrar
from pagina_inicio import pagina_inicio
from theme import inject_base_styles, render_nav_ativo, render_sidebar_logo

# (rótulo, restrito a RH/ADMIN) na ordem do Figma.
_MENU = [
    ("Início", False),
    ("Perfil", False),
    ("Ponto", False),
    ("Férias", False),
    ("Documentos", False),
    ("Pagamento", False),
    ("Central de Pendências", False),
    ("Trajetória", False),
    ("Auditoria", True),
    ("Regras", True),
]

logado = bool(st.session_state.get("token"))

st.set_page_config(
    page_title="ConectaRH",
    page_icon="🧭",
    layout="wide" if logado else "centered",
    initial_sidebar_state="expanded" if logado else "collapsed",
)

if not logado:
    st.navigation([st.Page(pagina_entrar, title="Entrar", url_path="entrar")], position="hidden").run()
    st.stop()

inject_base_styles("app")

pagina_atual = st.navigation(
    [st.Page(pagina_inicio, title="Início", url_path="inicio", default=True)],
    position="hidden",
)

perfil = str(st.session_state.usuario.get("perfil", "")).upper()
with st.sidebar:
    render_sidebar_logo()
    for rotulo, restrito in _MENU:
        if restrito and perfil not in ("RH", "ADMIN"):
            continue
        if rotulo == pagina_atual.title:
            render_nav_ativo(rotulo)
        elif st.button(rotulo, key=f"nav_{rotulo}", type="tertiary"):
            st.toast(f"A tela {rotulo} ainda está em construção.")

pagina_atual.run()
