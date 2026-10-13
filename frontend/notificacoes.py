"""
Sino de notificações do topo (Figma 197:77, "Dropdown/Notificações"; pedido do usuário em 12/10/2026).

O botão do sino mostra quantas não lidas há e abre o painel com as mais recentes: título, texto e quando. "Abrir →" marca
como lida e leva à tela do assunto (`notificacoes_modelo.destino`, pela marca `ir_*` que o app.py entende); "Marcar como
lida" e "Marcar todas como lidas" só marcam. O app.py registra `render_sino` no `theme.render_topbar` (`definir_sino`).
"""

import html
import time

import streamlit as st

from api_client import ApiError, marcar_notificacao_lida, marcar_todas_notificacoes_lidas, minhas_notificacoes
from notificacoes_modelo import destino, quando, resumo, rotulo_nao_lidas

_CACHE = "notif_cache"
_VALIDADE_CACHE_S = 30
_LIMITE_PAINEL = 15


def _carregar(token: str) -> dict | None:
    """A resposta de `minhas_notificacoes` por 30 s; None se não carregou (o sino aparece sem número)."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    try:
        dados = minhas_notificacoes(token)
    except ApiError:
        dados = None
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def invalidar() -> None:
    st.session_state.pop(_CACHE, None)


def _marcar(notificacao_id: int) -> None:
    try:
        marcar_notificacao_lida(st.session_state.token, notificacao_id)
    except ApiError as erro:
        st.session_state.notif_erro = erro.message
    invalidar()


def _marcar_todas() -> None:
    try:
        marcar_todas_notificacoes_lidas(st.session_state.token)
    except ApiError as erro:
        st.session_state.notif_erro = erro.message
    invalidar()


def _abrir(n: dict) -> None:
    """Marca como lida (se ainda não estava) e pede ao app.py a tela do assunto."""
    if not n.get("lida"):
        _marcar(n["id"])
    st.session_state[destino(n)] = True


def _preferencias() -> None:
    st.session_state.cfg_aba = "Notificações"
    st.session_state.ir_configuracoes = True


def _html_item(n: dict) -> str:
    lida = bool(n.get("lida"))
    return (f'<div class="crh-notif"><span class="p{" lida" if lida else ""}"></span><div>'
            f'<p class="t">{html.escape(n.get("titulo") or "Notificação")}</p>'
            f'<p class="m">{html.escape(n.get("mensagem") or "")}</p>'
            f'<p class="q">{html.escape(quando(n.get("criada_em")))}</p></div></div>')


def render_sino() -> None:
    token = st.session_state.get("token")
    dados = _carregar(token) if token else None
    total, lista = resumo(dados) if dados else (0, [])
    with st.popover(str(total) if total else "", icon=":material/notifications:", key="sino", help="Notificações"):
        with st.container(width=380, gap="small"):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.html('<p class="crh-cfg-titulo" style="margin:0">Notificações</p>', width="stretch")
                st.html(f'<span class="crh-selo {"amb" if total else "neu"}">{html.escape(rotulo_nao_lidas(total))}</span>', width="content")
            if erro := st.session_state.pop("notif_erro", None):
                st.html(f'<p class="crh-nota-ambar">{html.escape(erro)}</p>')
            if total:
                st.button("Marcar todas como lidas", type="tertiary", key="notif_todas", on_click=_marcar_todas)
            if dados is None:
                st.html('<p class="crh-meta">Não foi possível carregar as notificações agora.</p>')
            elif not lista:
                st.html('<p class="crh-meta">Nenhuma notificação.</p>')
            for n in lista[:_LIMITE_PAINEL]:
                nid = n.get("id")
                with st.container(key=f"notif_{'ok' if n.get('lida') else 'nl'}_{nid}", gap=None):
                    st.html(_html_item(n))
                    with st.container(horizontal=True, gap="medium"):
                        st.button("Abrir →", type="tertiary", key=f"notif_abrir_{nid}", on_click=_abrir, args=(n,))
                        if not n.get("lida"):
                            st.button("Marcar como lida", type="tertiary", key=f"notif_ler_{nid}", on_click=_marcar, args=(nid,))
            st.button("Preferências de notificação", type="tertiary", key="notif_prefs", on_click=_preferencias)
