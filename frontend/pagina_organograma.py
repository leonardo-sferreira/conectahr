"""
Página "Organograma" (Figma 224:3593; change organograma-hierarquia, D4). Pública para qualquer perfil logado.

Uma pessoa em foco por vez, em coluna (modelo pedido pelo usuário em 13/10/2026): o cartão do superior direto em cima,
uma linha, o cartão da pessoa em destaque, outra linha e os cartões de quem a tem como superior. Cada cartão mostra
nome, cargo e área, e clicar nele põe a pessoa em foco (sobe ou desce). Começa na própria pessoa; "Ir ao topo" mostra
quem não tem superior; "Minha posição" volta. A busca (nome, cargo ou nível) e o departamento mostram os cartões
encontrados. Só nome, cargo, nível e departamento vêm do backend (`organograma` GET).
"""

import html
import time

import streamlit as st

from api_client import ApiError, organograma
from foto_modelo import avatar_data_uri, avatar_html
from organograma_modelo import abaixo, buscar, montar, topo
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


def _linhas(p: dict) -> list[str]:
    """Cargo e área, cada um numa linha do cartão."""
    return [x for x in (p["cargo"], p["departamento"]) if x] or ["—"]


def _cartao_destaque(p: dict, voce: bool) -> None:
    detalhes = "".join(f'<p class="d">{html.escape(x)}</p>' for x in _linhas(p))
    st.html(f'<div class="crh-org-foco">{avatar_html(p["nome"], p.get("foto_url"), 56, "crh-org-foco-av")}<div><p class="t">{html.escape(p["nome"])}'
            f'{" (você)" if voce else ""}</p>{detalhes}</div></div>')


def _cartao(p: dict, meu_id, chave: str) -> None:
    """Cartão clicável: o nome em negrito e, embaixo, o cargo e a área (quebra de linha pelo CSS `pre-line`)."""
    # A foto (ou o círculo das iniciais) entra como imagem no rótulo, que é Markdown (change foto-de-perfil).
    imagem = p.get("foto_url") or avatar_data_uri(p["nome"])
    rotulo = f'![]({imagem}) **{p["nome"]}{" (você)" if p["id"] == meu_id else ""}**\n' + "\n".join(_linhas(p))
    st.button(rotulo, key=chave, on_click=_focar, args=(p["id"],), width="content")


def _linha_vertical() -> None:
    st.html('<div class="crh-org-conector"></div>')


def _fileira(lista: list[dict], meu_id, prefixo: str) -> None:
    with st.container(horizontal=True, horizontal_alignment="center", gap="medium", key=f"{prefixo}_fileira"):
        for p in lista:
            _cartao(p, meu_id, f"{prefixo}_p_{p['id']}")


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
            st.button("Ir ao topo", key="org_topo", on_click=_focar, args=(TOPO,))
            if meu_id in pessoas:
                st.button("Minha posição", key="org_minha", on_click=_focar, args=(meu_id,))

        if busca.strip() or dep:
            achados = buscar(pessoas, busca, dep)
            st.html(f'<p class="crh-cfg-titulo" style="margin:4px 0 0">Resultados ({len(achados)})</p>')
            if not achados:
                st.html('<p class="crh-meta">Ninguém encontrado com essa busca.</p>')
            _fileira(achados, meu_id, "org_res")
            return

        foco = st.session_state.org_foco
        with st.container(horizontal_alignment="center", gap=None, key="org_arvore"):
            if foco == TOPO:
                st.html('<p class="crh-cfg-titulo" style="margin:4px 0 12px;text-align:center">Topo da empresa</p>')
                _fileira(topo(pessoas), meu_id, "org_topo")
                return
            p = pessoas[foco]
            superior = pessoas.get(p["superior_id"])
            if superior:
                _cartao(superior, meu_id, f"org_sup_{superior['id']}")
                _linha_vertical()
            _cartao_destaque(p, p["id"] == meu_id)
            equipe = abaixo(pessoas, foco)
            if equipe:
                _linha_vertical()
                _fileira(equipe, meu_id, "org_eq")
            else:
                st.html(f'<p class="crh-meta" style="text-align:center;margin-top:12px">Ninguém tem {html.escape(p["nome"].split()[0])} como superior direto.</p>')
        st.html('<p class="crh-meta" style="margin-top:12px;text-align:center">Clique numa pessoa para ver quem está acima e abaixo dela.</p>')
