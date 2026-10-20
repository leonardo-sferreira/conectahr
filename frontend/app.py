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

from api_client import ApiError, auth_me, folha_pessoas, logout
from campos import instalar as instalar_campos
from campos import nova_rodada
from notificacoes import render_sino
from pagina_auditoria import pagina_auditoria
from pagina_ausencias import pagina_ausencias
from pagina_aviso import pagina_aviso_logado, pagina_aviso_publico
from pagina_beneficios import pagina_beneficios
from pagina_central import pagina_central
from pagina_ciclos_avaliacao import pagina_ciclos_avaliacao
from pagina_colaboradores import pagina_colaboradores
from pagina_conferencia_documentos import pagina_conferencia_documentos
from pagina_configuracoes import pagina_configuracoes
from pagina_documentos import pagina_documentos
from pagina_entrar import pagina_entrar
from pagina_ferias import pagina_ferias
from pagina_estrutura import pagina_estrutura
from pagina_faq import pagina_faq
from pagina_folha_ponto import pagina_folha_ponto
from pagina_inicio import pagina_inicio
from pagina_meu_onboarding import pagina_meu_onboarding
from pagina_metas_ciclo import pagina_metas_ciclo
from pagina_metas_equipe import pagina_metas_equipe
from pagina_onboarding import pagina_onboarding
from pagina_organograma import pagina_organograma
from pagina_pagamento import pagina_lancamento_pagamentos, pagina_pagamento
from pagina_perfil import pagina_perfil
from pagina_ponto import pagina_ponto
from pagina_solicitacoes import pagina_solicitacoes
from pagina_trajetoria import pagina_trajetoria
from pagina_usuarios import pagina_usuarios
from sessao import encerrar_com_aviso, limpar_sessao, sessao_terminou
from theme import definir_sino, inject_base_styles, render_nav_ativo, render_sidebar_logo

# (rótulo, restrito a RH/ADMIN) na ordem do Figma.
_MENU = [
    ("Início", False),
    ("Perfil", False),
    ("Ponto", False),
    ("Férias", False),
    ("Documentos", False),
    ("Pagamento", False),
    ("Benefícios", False),
    ("Central de Pendências", False),
    ("Trajetória", False),
    # Vagas internas: o sistema de vagas fica em outro endereço, ainda não ligado; a opção só aparece no menu.
    ("Vagas internas", False),
    ("Auditoria", True),
    ("Regras", True),
]
# Grupo "RH" do menu (Figma 418:1108 e Design System 314:786), só para RH e Admin.
_MENU_RH = [
    "Colaboradores",
    "Solicitações ao RH",
    "Folha de ponto",
    "Ausências",
    "Conferência de documentos",
    # Lançar holerites e informes dos colaboradores; os próprios ficam em "Pagamento" (pedido do usuário, 20/10/2026).
    "Lançamento de pagamentos",
    "Desligamentos",
    "Comunicados e FAQ",
    "Pesquisas de clima",
    "Ciclos de avaliação",
    "Pedidos LGPD",
    # Feriados, níveis da hierarquia e cargos (change organograma-hierarquia): o RH também mantém.
    "Estrutura da empresa",
]
# Grupo "Equipe" do menu (Figma 241:560): o Gestor vê todo; quem é superior direto sem o perfil Gestor (tarefa 83) vê só a folha.
_MENU_EQUIPE = [
    "Minha equipe",
    "Folha de ponto da equipe",
    "Avaliações da equipe",
    # Ciclo anual de metas da equipe, com o feedback de cada etapa (change ciclo-de-metas).
    "Metas da equipe",
    "Delegações",
    "Indicadores da equipe",
]
# Grupo "Admin" do menu (Figma 246:612), só para o Admin.
_MENU_ADMIN = [
    "Usuários e perfis",
    "Sessões ativas",
    "Indicadores gerais",
    "Integrações e e-mails",
]

# O sino do topo fala com a API; o tema só o desenha (render_topbar).
definir_sino(render_sino)
# Nenhum campo de texto aceita emoji e cada campo aceita só o seu tipo (pedido do usuário, 20/10/2026; campos.py):
# aviso embaixo do campo e o botão principal não grava. Sem callback: dentro de st.dialog ele apagava a página.
instalar_campos()
nova_rodada()

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
PG_PAGAMENTO = st.Page(pagina_pagamento, title="Pagamento", url_path="pagamento")
PG_LANCAMENTOS = st.Page(pagina_lancamento_pagamentos, title="Lançamento de pagamentos", url_path="lancamento-de-pagamentos")
PG_CENTRAL = st.Page(pagina_central, title="Central de Pendências", url_path="central-de-pendencias")
PG_AUSENCIAS = st.Page(pagina_ausencias, title="Ausências", url_path="ausencias")
PG_COLABORADORES = st.Page(pagina_colaboradores, title="Colaboradores", url_path="colaboradores")
PG_USUARIOS = st.Page(pagina_usuarios, title="Usuários e perfis", url_path="usuarios-e-perfis")
PG_BENEFICIOS = st.Page(pagina_beneficios, title="Benefícios", url_path="beneficios")
PG_FOLHA = st.Page(pagina_folha_ponto, title="Folha de ponto", url_path="folha-de-ponto")
PG_SOLICITACOES = st.Page(pagina_solicitacoes, title="Solicitações ao RH", url_path="solicitacoes-ao-rh")
PG_CONFERENCIA = st.Page(pagina_conferencia_documentos, title="Conferência de documentos", url_path="conferencia-de-documentos")
PG_ESTRUTURA = st.Page(pagina_estrutura, title="Estrutura da empresa", url_path="estrutura-da-empresa")
PG_FAQ = st.Page(pagina_faq, title="Comunicados e FAQ", url_path="comunicados-e-faq")
PG_ORGANOGRAMA = st.Page(pagina_organograma, title="Organograma", url_path="organograma")
PG_AUDITORIA = st.Page(pagina_auditoria, title="Auditoria", url_path="auditoria")
PG_METAS_CICLO = st.Page(pagina_metas_ciclo, title="Metas do ciclo", url_path="metas-do-ciclo")
PG_CICLOS = st.Page(pagina_ciclos_avaliacao, title="Ciclos de avaliação", url_path="ciclos-de-avaliacao")
PG_METAS_EQUIPE = st.Page(pagina_metas_equipe, title="Metas da equipe", url_path="metas-da-equipe")
PG_TRAJETORIA = st.Page(pagina_trajetoria, title="Trajetória", url_path="trajetoria")
pagina_atual = st.navigation(
    [PG_INICIO, PG_PERFIL, PG_PONTO, PG_FERIAS, PG_PAGAMENTO, PG_LANCAMENTOS, PG_MEU_ONBOARDING, PG_DOCUMENTOS, PG_CONFIGURACOES, PG_AVISO, PG_CENTRAL, PG_AUSENCIAS, PG_COLABORADORES, PG_USUARIOS, PG_SOLICITACOES, PG_FOLHA, PG_BENEFICIOS, PG_CONFERENCIA, PG_ESTRUTURA, PG_FAQ, PG_ORGANOGRAMA, PG_TRAJETORIA, PG_METAS_CICLO, PG_CICLOS, PG_METAS_EQUIPE, PG_AUDITORIA], position="hidden"
)

# Atalhos pedidos por uma página (o st.Page só existe aqui).
_ATALHOS = {
    "ir_meu_onboarding": PG_MEU_ONBOARDING,
    "ir_inicio": PG_INICIO,
    "ir_documentos": PG_DOCUMENTOS,
    "ir_configuracoes": PG_CONFIGURACOES,
    "ir_aviso": PG_AVISO,
    "ir_central": PG_CENTRAL,
    "ir_solicitacoes": PG_SOLICITACOES,
    "ir_faq": PG_FAQ,
    "ir_organograma": PG_ORGANOGRAMA,
    # Destinos do sino de notificações (notificacoes_modelo.destino).
    "ir_ferias": PG_FERIAS,
    "ir_ponto": PG_PONTO,
    "ir_folha": PG_FOLHA,
    "ir_beneficios": PG_BENEFICIOS,
    "ir_ausencias": PG_AUSENCIAS,
    "ir_conferencia": PG_CONFERENCIA,
    "ir_perfil": PG_PERFIL,
    "ir_pagamento": PG_PAGAMENTO,
    "ir_trajetoria": PG_TRAJETORIA,
    "ir_metas_ciclo": PG_METAS_CICLO,
    "ir_metas_equipe": PG_METAS_EQUIPE,
}
for marca, destino in _ATALHOS.items():
    if st.session_state.pop(marca, False):
        st.switch_page(destino)

# Páginas do menu lateral que já existem; as outras ainda mostram "em construção".
_PAGINAS_DO_MENU = {"Início": PG_INICIO, "Perfil": PG_PERFIL, "Ponto": PG_PONTO, "Férias": PG_FERIAS, "Documentos": PG_DOCUMENTOS, "Pagamento": PG_PAGAMENTO, "Lançamento de pagamentos": PG_LANCAMENTOS, "Benefícios": PG_BENEFICIOS, "Central de Pendências": PG_CENTRAL, "Auditoria": PG_AUDITORIA, "Trajetória": PG_TRAJETORIA, "Ausências": PG_AUSENCIAS, "Colaboradores": PG_COLABORADORES, "Solicitações ao RH": PG_SOLICITACOES, "Folha de ponto": PG_FOLHA, "Folha de ponto da equipe": PG_FOLHA, "Usuários e perfis": PG_USUARIOS, "Conferência de documentos": PG_CONFERENCIA, "Estrutura da empresa": PG_ESTRUTURA, "Comunicados e FAQ": PG_FAQ, "Ciclos de avaliação": PG_CICLOS, "Metas da equipe": PG_METAS_EQUIPE}

# "Meu onboarding" é uma tela do Início: o item ativo do menu continua sendo "Início" (Figma 309:1048).
# Configurações e o aviso não são itens do menu: nenhum fica ativo (Figma 286:878 e 285:1073).
ativo_no_menu = {"Meu onboarding": "Início", "Organograma": "Perfil", "Metas do ciclo": "Trajetória"}.get(pagina_atual.title, pagina_atual.title)
perfil = str(st.session_state.usuario.get("perfil", "")).upper()

# Quem é superior direto de alguém decide e vê a folha da equipe, qualquer que seja o perfil (tarefa 83).
# Conferido uma vez por sessão; se a chamada falhar, o menu fica como o do perfil.
if perfil not in ("RH", "ADMIN", "GESTOR") and "tem_equipe" not in st.session_state:
    try:
        st.session_state.tem_equipe = any(not p.get("e_voce") for p in folha_pessoas(st.session_state.token).get("pessoas") or [])
    except ApiError:
        st.session_state.tem_equipe = False
# Quem é superior direto também acompanha as metas da equipe e dá feedback (change ciclo-de-metas).
menu_equipe = _MENU_EQUIPE if perfil == "GESTOR" else ["Folha de ponto da equipe", "Metas da equipe"] if st.session_state.get("tem_equipe") else []
if ativo_no_menu == "Folha de ponto" and menu_equipe:
    ativo_no_menu = "Folha de ponto da equipe"

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
            if rotulo == "Vagas internas":
                st.toast("Vagas internas: em breve, as vagas abertas da empresa vão abrir aqui.")
            else:
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
    if menu_equipe:
        st.html('<p class="crh-nav-grupo">Equipe</p>')
        for rotulo in menu_equipe:
            if rotulo == ativo_no_menu:
                render_nav_ativo(rotulo)
            elif st.button(rotulo, key=f"nav_{rotulo}", type="tertiary"):
                if rotulo in _PAGINAS_DO_MENU:
                    st.switch_page(_PAGINAS_DO_MENU[rotulo])
                st.toast(f"A tela {rotulo} ainda está em construção.")
    if perfil == "ADMIN":
        st.html('<p class="crh-nav-grupo">Admin</p>')
        for rotulo in _MENU_ADMIN:
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
