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

Sem login também existe o "Aviso de privacidade" (Figma 285:874), aberto pelo link da tela
Entrar. As páginas pedem a troca de página deixando uma marca em `st.session_state` (`ir_*`),
porque o st.Page só existe aqui; "Sair da conta" (menu da conta) também passa por aqui.

A lista de itens por perfil é só conveniência de navegação — a autorização
real continua sendo do backend.
"""

import streamlit as st

from api_client import ApiError, auth_me, logout
from pagina_aviso import pagina_aviso_logado, pagina_aviso_publico
from pagina_conferencia_documentos import pagina_conferencia_documentos
from pagina_configuracoes import pagina_configuracoes
from pagina_documentos import pagina_documentos
from pagina_entrar import pagina_entrar
from pagina_ferias import pagina_ferias
from pagina_inicio import pagina_inicio
from pagina_meu_onboarding import pagina_meu_onboarding
from pagina_onboarding import pagina_onboarding
from pagina_perfil import pagina_perfil
from pagina_ponto import pagina_ponto
from sessao import encerrar_com_aviso, limpar_sessao, sessao_terminou
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
# Grupo "RH" do menu (Figma 418:1108 e Design System 314:786), só para RH e Admin.
_MENU_RH = [
    "Colaboradores",
    "Ausências",
    "Conferência de documentos",
    "Desligamentos",
    "Comunicados e FAQ",
    "Pesquisas de clima",
    "Ciclos de avaliação",
    "Pedidos LGPD",
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

# "Sair da conta" (menu da conta, Figma 198:158): encerra a sessão no backend e volta a Entrar.
if logado and st.session_state.pop("sair_da_conta", False):
    try:
        logout(st.session_state.token)
    except ApiError:
        pass  # A sessão local é apagada de qualquer jeito; a do backend vence no prazo.
    limpar_sessao()
    st.session_state.auth_step = "login"
    st.session_state.aviso_login = "Você saiu da sua conta."
    st.rerun()

if not logado:
    PG_ENTRAR = st.Page(pagina_entrar, title="Entrar", url_path="entrar", default=True)
    PG_AVISO_PUBLICO = st.Page(pagina_aviso_publico, title="Aviso de privacidade", url_path="aviso-de-privacidade")
    pagina_publica = st.navigation([PG_ENTRAR, PG_AVISO_PUBLICO], position="hidden")
    if st.session_state.pop("ir_aviso", False):
        st.switch_page(PG_AVISO_PUBLICO)
    if st.session_state.pop("ir_entrar", False):
        st.switch_page(PG_ENTRAR)
    pagina_publica.run()
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
PG_DOCUMENTOS = st.Page(pagina_documentos, title="Documentos", url_path="documentos")
PG_CONFIGURACOES = st.Page(pagina_configuracoes, title="Configurações", url_path="configuracoes")
PG_AVISO = st.Page(pagina_aviso_logado, title="Aviso de privacidade", url_path="aviso-de-privacidade")
PG_PERFIL = st.Page(pagina_perfil, title="Perfil", url_path="perfil")
PG_PONTO = st.Page(pagina_ponto, title="Ponto", url_path="ponto")
PG_FERIAS = st.Page(pagina_ferias, title="Férias", url_path="ferias")
PG_CONFERENCIA = st.Page(pagina_conferencia_documentos, title="Conferência de documentos", url_path="conferencia-de-documentos")
pagina_atual = st.navigation(
    [PG_INICIO, PG_PERFIL, PG_PONTO, PG_FERIAS, PG_MEU_ONBOARDING, PG_DOCUMENTOS, PG_CONFIGURACOES, PG_AVISO, PG_CONFERENCIA], position="hidden"
)

# Atalhos pedidos por uma página (o st.Page só existe aqui).
_ATALHOS = {
    "ir_meu_onboarding": PG_MEU_ONBOARDING,
    "ir_inicio": PG_INICIO,
    "ir_documentos": PG_DOCUMENTOS,
    "ir_configuracoes": PG_CONFIGURACOES,
    "ir_aviso": PG_AVISO,
}
for marca, destino in _ATALHOS.items():
    if st.session_state.pop(marca, False):
        st.switch_page(destino)

# Páginas do menu lateral que já existem; as outras ainda mostram "em construção".
_PAGINAS_DO_MENU = {"Início": PG_INICIO, "Perfil": PG_PERFIL, "Ponto": PG_PONTO, "Férias": PG_FERIAS, "Documentos": PG_DOCUMENTOS, "Conferência de documentos": PG_CONFERENCIA}

# "Meu onboarding" é uma tela do Início: o item ativo do menu continua sendo "Início" (Figma 309:1048).
# Configurações e o aviso não são itens do menu: nenhum fica ativo (Figma 286:878 e 285:1073).
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
            if rotulo in _PAGINAS_DO_MENU:
                st.switch_page(_PAGINAS_DO_MENU[rotulo])
            st.toast(f"A tela {rotulo} ainda está em construção.")
    if perfil in ("RH", "ADMIN"):
        st.html('<p class="crh-nav-grupo">RH</p>')
        for rotulo in _MENU_RH:
            if rotulo == ativo_no_menu:
                render_nav_ativo(rotulo)
            elif st.button(rotulo, key=f"nav_{rotulo}", type="tertiary"):
                if rotulo in _PAGINAS_DO_MENU:
                    st.switch_page(_PAGINAS_DO_MENU[rotulo])
                st.toast(f"A tela {rotulo} ainda está em construção.")

pagina_atual.run()

# Uma chamada da página recebeu 401 (sessão encerrada em outro lugar): login com aviso.
if st.session_state.get("sessao_expirada"):
    encerrar_com_aviso()
    st.rerun()
