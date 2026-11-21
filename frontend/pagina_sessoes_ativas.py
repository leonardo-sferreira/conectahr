"""
Página "Sessões ativas" do grupo Admin (Figma 249:6819; tarefa 65 da change concluir-frontend-streamlit). Só o Admin.

Lista as sessões abertas de todas as contas (nome, perfil, navegador e início), com busca por nome e filtro por perfil.
"Encerrar" pede confirmação e revoga a sessão na hora; a ação vai para a auditoria (`encerrar_sessao_admin`). A sessão
do próprio Admin aparece marcada e não tem "Encerrar": para ela existe "Sair". Endpoints novos:
`admin/sessoes_ativas` GET e `admin/sessoes/{id}/encerrar` POST.

Diferenças do Figma:
- a coluna "Local" não existe, porque o sistema não guarda a localização; o IP também não aparece (minimização);
- o quadro "Acesso fora do comum" não existe, porque o backend ainda não detecta acesso suspeito;
- o quadro "Backend" do Figma era uma nota de projeto e saiu, porque o endpoint agora existe.
"""

import html
import time
from datetime import datetime

import streamlit as st

import sessoes_admin_modelo as sm
from api_client import ApiError, encerrar_sessao_admin, sessoes_ativas
from delegacoes_modelo import BRASILIA
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    item = st.session_state.get("sa_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = sessoes_ativas(token)
    st.session_state.sa_cache = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("sa_modal", None)


@st.dialog("Encerrar sessão?", width="small", on_dismiss=_fechar)
def _modal_encerrar(linha: dict) -> None:
    st.html('<div class="crh-lgpd-resumo">'
            f"<div><span>Conta</span><b>{html.escape(linha['nome'])}</b></div>"
            f"<div><span>Navegador</span><b>{html.escape(linha['dispositivo'])}</b></div>"
            f"<div><span>Início</span><b>{html.escape(linha['inicio'])}</b></div></div>"
            '<p class="crh-alerta-inline">A pessoa sai do sistema nesse navegador na próxima ação e precisa entrar de novo.</p>'
            '<p class="crh-meta">O encerramento fica na auditoria.</p>')
    slot = st.empty()
    with st.container(horizontal=True):
        if st.button("Cancelar", key="sa_cancelar"):
            _fechar()
            st.rerun()
        with st.container(key="ret_perigo", width="content"):
            clicou = st.button("Encerrar sessão", type="primary", key="sa_ok")
    if clicou:
        try:
            encerrar_sessao_admin(st.session_state.token, linha["id"])
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        for chave in ("sa_modal", "sa_cache"):
            st.session_state.pop(chave, None)
        st.session_state.aviso_toast = f"Sessão de {linha['nome']} encerrada."
        st.rerun()


def pagina_sessoes_ativas() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Sessões ativas", "Onde cada conta está conectada agora")
    if str(usuario.get("perfil", "")).upper() != "ADMIN":
        alerta(st.empty(), "erro", "Esta tela é só do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    sessoes = dados.get("sessoes") or []
    render_indicadores([("Sessões abertas", str(len(sessoes)), ""), ("Contas conectadas", str(sm.contas(sessoes)), ""),
                        ("Validade de cada sessão", "1 hora", "")])
    with st.container(horizontal=True, vertical_alignment="center"):
        busca = st.text_input("Buscar usuário", key="sa_busca", placeholder="Buscar usuário", label_visibility="collapsed", width=300)
        st.space("stretch")
        perfil = st.selectbox("Perfil", [None] + list(sm.PERFIS), format_func=lambda p: "Perfil: Todos" if p is None else f"Perfil: {sm.PERFIS[p]}",
                              key="sa_perfil", label_visibility="collapsed", width=200)
    linhas = sm.linhas(sessoes, datetime.now(BRASILIA).date(), busca, perfil)
    pesos = [2.4, 2.4, 1.6, 1.2]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Usuário", "Dispositivo", "Início", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">' + ("Nenhuma sessão com esse filtro." if sessoes else "Nenhuma sessão aberta.") + "</p>")
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p><p class="d">{html.escape(l["perfil"])}</p></div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(l["dispositivo"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["inicio"])}</p>')
                with col[3]:
                    if l["atual"]:
                        st.html('<span class="crh-selo ok">Esta sessão</span>')
                    elif st.button("Encerrar", key=f"sa_encerrar_{l['id']}", type="tertiary"):
                        st.session_state.sa_modal = l["id"]
                        st.rerun()
    st.html('<p class="crh-meta">A localização e o IP não aparecem aqui. '
            "Cada pessoa também vê e encerra as próprias sessões em Configurações → Segurança.</p>")
    if alvo := st.session_state.get("sa_modal"):
        linha = next((l for l in linhas if l["id"] == alvo), None)
        if linha:
            _modal_encerrar(linha)
        else:
            _fechar()
