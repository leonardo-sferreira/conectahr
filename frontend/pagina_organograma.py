"""
Página "Organograma" (Figma 224:3593; change organograma-hierarquia, D4). Pública para qualquer perfil logado.

Uma pessoa em foco por vez: o caminho do topo até ela (clicável), o superior direto acima, o cartão dela e, abaixo,
quem a tem como superior, agrupado pelo nível do cargo. Começa na própria pessoa; "Topo" mostra quem não tem
superior; "Minha posição" volta. A busca (nome, cargo ou nível) e o departamento mostram uma lista que leva ao foco.
Só nome, cargo, nível e departamento (`organograma` GET).
"""

import html
import time

import streamlit as st

from api_client import ApiError, organograma
from organograma_modelo import abaixo, buscar, caminho, detalhe, montar, por_nivel, topo
from theme import alerta, render_hero, render_topbar

_CACHE = "org_cache"
_VALIDADE_CACHE_S = 60
TOPO = "topo"


def _carregar(token: str) -> dict:
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = organograma(token)
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _focar(pid) -> None:
    """Põe a pessoa (ou o topo) em foco e limpa a busca."""
    st.session_state.org_foco = pid
    st.session_state.org_busca = ""
    st.session_state.org_dep = None


def _cartao_destaque(p: dict, voce: bool) -> None:
    st.html(f'<div class="crh-org-foco"><span class="av">{html.escape(p["iniciais"])}</span><div>'
            f'<p class="t">{html.escape(p["nome"])}{" (você)" if voce else ""}</p>'
            f'<p class="d">{html.escape(detalhe(p))}</p></div></div>')


def _botao_pessoa(p: dict, meu_id, chave: str) -> None:
    rotulo = f'**{p["nome"]}{" (você)" if p["id"] == meu_id else ""}** — {detalhe(p)}'
    st.button(rotulo, key=chave, on_click=_focar, args=(p["id"],), width="content")


def _grupos(pessoas_lista: list[dict], meu_id, prefixo: str) -> None:
    for nivel, grupo in por_nivel(pessoas_lista):
        st.html(f'<p class="crh-meta" style="margin:8px 0 0">{html.escape(nivel)} ({len(grupo)})</p>')
        with st.container(horizontal=True, gap="small", key=f"{prefixo}_{nivel}"):
            for p in grupo:
                _botao_pessoa(p, meu_id, f"{prefixo}_p_{p['id']}")


def pagina_organograma() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    render_hero("Organograma", "Quem é quem na empresa")
    with st.spinner("Carregando o organograma..."):
        try:
            org, erro = _carregar(token), None
        except ApiError as falha:
            org, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "erro", erro.message)
        return
    pessoas = montar(org)
    if not pessoas:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Ninguém no organograma ainda.</p></div>')
        return
    meu_id = usuario.get("colaborador_id")
    if st.session_state.get("org_foco") not in pessoas and st.session_state.get("org_foco") != TOPO:
        st.session_state.org_foco = meu_id if meu_id in pessoas else TOPO
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}

    with st.container(key="org_card"):
        with st.container(horizontal=True, vertical_alignment="center", key="org_filtros"):
            busca = st.text_input("Busca", placeholder="⌕  Buscar pessoa ou cargo", key="org_busca", label_visibility="collapsed")
            dep = st.selectbox("Departamento", [None] + sorted(deps, key=lambda d: deps[d] or ""), key="org_dep", label_visibility="collapsed",
                               format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}", width=260)
            if meu_id in pessoas:
                st.button("Minha posição", key="org_minha", on_click=_focar, args=(meu_id,))

        if busca.strip() or dep:
            achados = buscar(pessoas, busca, dep)
            st.html(f'<p class="crh-cfg-titulo" style="margin:4px 0 0">Resultados ({len(achados)})</p>')
            if not achados:
                st.html('<p class="crh-meta">Ninguém encontrado com essa busca.</p>')
            _grupos(achados, meu_id, "org_res")
            return

        foco = st.session_state.org_foco
        trilha = [] if foco == TOPO else caminho(pessoas, foco)
        with st.container(horizontal=True, gap="small", vertical_alignment="center", key="org_trilha"):
            st.button("Topo", key="org_trilha_topo", type="tertiary", on_click=_focar, args=(TOPO,))
            for p in trilha:
                st.html('<span class="crh-meta">›</span>', width="content")
                st.button(p["nome"], key=f"org_trilha_{p['id']}", type="tertiary", on_click=_focar, args=(p["id"],))

        if foco == TOPO:
            st.html('<p class="crh-cfg-titulo" style="margin:4px 0 0">Topo da empresa</p>')
            _grupos(topo(pessoas), meu_id, "org_topo")
            return

        p = pessoas[foco]
        superior = pessoas.get(p["superior_id"])
        if superior:
            st.html('<p class="crh-meta" style="margin:4px 0 0">Superior direto</p>')
            _botao_pessoa(superior, meu_id, f"org_sup_{superior['id']}")
        st.html('<p class="crh-meta" style="margin:4px 0 0">Posição</p>')
        _cartao_destaque(p, p["id"] == meu_id)
        equipe = abaixo(pessoas, foco)
        primeiro_nome = p["nome"].split()[0]
        if equipe:
            st.html(f'<p class="crh-cfg-titulo" style="margin:8px 0 0">Abaixo de {html.escape(primeiro_nome)} ({len(equipe)})</p>')
            _grupos(equipe, meu_id, "org_eq")
        else:
            st.html(f'<p class="crh-meta">Ninguém tem {html.escape(primeiro_nome)} como superior direto.</p>')
        st.html('<p class="crh-meta" style="margin-top:8px">Clique numa pessoa para ver o superior e quem está abaixo dela.</p>')
