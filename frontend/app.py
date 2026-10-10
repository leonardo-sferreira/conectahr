"""
ConectaRH — ponto de entrada do frontend Streamlit.

Navegação com st.navigation/st.Page (design.md do change
implementar-frontend-streamlit): sem token só a página "Entrar" existe; com
token, as páginas da área logada. O menu nativo fica oculto (position="hidden")
e a sidebar é desenhada aqui, fiel ao protótipo Figma (nó 62:38): logo, item
ativo em âmbar e os demais itens em cinza.

Guarda de sessão: se o token venceu, foi revogado ou encerrado em outro
dispositivo (resposta 401 da API), a pessoa volta para "Entrar" com o aviso
"Sua sessão terminou" (Figma F01, nó 224:619). Logo depois da troca da senha
temporária, quem tem onboarding passa pela página "Onboarding" antes do Início
(Figma F01, caminho "Primeiro acesso").

A lista de itens por perfil é só conveniência de navegação — a autorização
real continua sendo do backend.
"""

import streamlit as st

from api_client import ApiError, auth_me
from pagina_entrar import pagina_entrar
from pagina_inicio import pagina_inicio
from pagina_meu_onboarding import pagina_meu_onboarding
from pagina_onboarding import pagina_onboarding
from sessao import encerrar_com_aviso, sessao_terminou
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
em_onboarding = logado and bool(st.session_state.get("onboarding_pendente"))

st.set_page_config(
    page_title="ConectaRH",
    page_icon="🧭",
    layout="wide" if logado and not em_onboarding else "centered",
    initial_sidebar_state="expanded" if logado and not em_onboarding else "collapsed",
)

# Token vencido pelo relógio ou rejeitado pela API na rodada anterior: volta ao login com aviso.
if logado and sessao_terminou():
    encerrar_com_aviso()
    st.rerun()

if not logado:
    st.navigation([st.Page(pagina_entrar, title="Entrar", url_path="entrar")], position="hidden").run()
    st.stop()

# Uma consulta a auth/me por sessão confere que o token ainda vale (a sessão pode ter sido
# revogada em outro dispositivo logo depois do login). Falha de rede só tenta de novo depois;
# 401 marca "sessao_expirada" e a pessoa volta ao login com aviso.
if not st.session_state.get("sessao_validada"):
    try:
        auth_me(st.session_state.token)
        st.session_state.sessao_validada = True
    except ApiError:
        pass
    if sessao_terminou():
        encerrar_com_aviso()
        st.rerun()

if em_onboarding:
    st.navigation([st.Page(pagina_onboarding, title="Onboarding", url_path="onboarding")], position="hidden").run()
    if st.session_state.get("sessao_expirada"):
        encerrar_com_aviso()
        st.rerun()
    st.stop()

inject_base_styles("app")

PG_INICIO = st.Page(pagina_inicio, title="Início", url_path="inicio", default=True)
PG_MEU_ONBOARDING = st.Page(pagina_meu_onboarding, title="Meu onboarding", url_path="meu-onboarding")
pagina_atual = st.navigation([PG_INICIO, PG_MEU_ONBOARDING], position="hidden")

# Atalhos pedidos por uma página (o st.Page só existe aqui): Início <-> Meu onboarding.
if st.session_state.pop("ir_meu_onboarding", False):
    st.switch_page(PG_MEU_ONBOARDING)
if st.session_state.pop("ir_inicio", False):
    st.switch_page(PG_INICIO)

# "Meu onboarding" é uma tela do Início: o item ativo do menu continua sendo "Início" (Figma 309:1048).
ativo_no_menu = {"Meu onboarding": "Início"}.get(pagina_atual.title, pagina_atual.title)

perfil = str(st.session_state.usuario.get("perfil", "")).upper()
with st.sidebar:
    render_sidebar_logo()
    for rotulo, restrito in _MENU:
        if restrito and perfil not in ("RH", "ADMIN"):
            continue
        if rotulo == ativo_no_menu:
            render_nav_ativo(rotulo)
        elif st.button(rotulo, key=f"nav_{rotulo}", type="tertiary"):
            st.toast(f"A tela {rotulo} ainda está em construção.")

pagina_atual.run()

# Uma chamada da página recebeu 401 (sessão encerrada em outro lugar): login com aviso.
if st.session_state.get("sessao_expirada"):
    encerrar_com_aviso()
    st.rerun()
