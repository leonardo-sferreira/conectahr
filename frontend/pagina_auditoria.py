"""
Página "Auditoria" (Figma 225:6784; tarefas 34 e 35 de concluir-frontend-streamlit). Só RH e Admin; a autorização é do
backend (`auditoria` GET).

Filtros do Figma (recurso, ação, resultado e usuário) e o período (últimos 7, 30 ou 90 dias, ou o último ano); a
tabela mostra até 300 eventos, os mais recentes primeiro. "Ver" abre os detalhes do evento (registro, valores anterior
e novo, já mascarados, e IP), que o Figma não desenhou (docs/figma-pendencias.md).
"""

import html
import time

import streamlit as st

from api_client import ApiError, auditoria
from auditoria_modelo import PERIODOS, RESULTADOS, detalhes, linhas, opcoes_usuarios
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 20


def _carregar(token: str, filtros: dict) -> dict:
    """Uma consulta por combinação de filtros, guardada por 20 s (limite de requisições do Xano)."""
    chave = "aud_cache_" + "|".join(f"{k}={v}" for k, v in sorted(filtros.items()))
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = auditoria(token, **filtros)
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("aud_detalhe", None)


@st.dialog("Detalhes do evento", width="medium", on_dismiss=_fechar)
def _modal_detalhe(linha: dict) -> None:
    campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in detalhes(linha))
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')
    st.html('<p class="crh-meta">Valores pessoais aparecem mascarados, como foram gravados.</p>')
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Fechar", key="aud_fechar"):
            _fechar()
            st.rerun()


def _tabela(itens: list[dict]) -> None:
    pesos = [1.5, 1.9, 2.2, 1.4, 2.6, 1, 0.7]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Data / hora", "Usuário", "Ação", "Recurso", "Justificativa", "Resultado", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not itens:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum evento neste filtro e período.</p>')
        for i, l in enumerate(itens):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                for coluna, texto in zip(c[:5], (l["quando"], l["usuario"], l["acao"], l["recurso"], l["justificativa"])):
                    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')
                c[5].html(f'<p class="crh-aud-res {l["tom"]}">{html.escape(l["resultado"])}</p>')
                with c[6]:
                    if st.button("Ver", type="tertiary", key=f"aud_ver_{l['id']}"):
                        st.session_state.aud_detalhe = l["id"]
                        st.rerun()


def pagina_auditoria() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    render_hero("Auditoria", "Trilha completa de ações no sistema — autor, data e resultado")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return

    # Opções dos filtros: vêm da consulta sem filtro do período (recursos, ações e usuários que aparecem nele).
    dias = st.session_state.get("aud_dias", 30)
    try:
        with st.spinner("Carregando a trilha..."):
            base = _carregar(token, {"dias": dias})
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    usuarios = base.get("usuarios") or []
    pessoas = opcoes_usuarios(base.get("usuarios_na_janela"), usuarios)
    with st.container(horizontal=True, vertical_alignment="center", key="aud_filtros"):
        recurso = st.selectbox("Recurso", [None] + sorted(base.get("recursos") or []), format_func=lambda r: "Recurso: todos" if r is None else f"Recurso: {r}",
                               key="aud_recurso", label_visibility="collapsed", width=210)
        acao = st.selectbox("Ação", [None] + sorted(base.get("acoes") or []), format_func=lambda a: "Ação: todas" if a is None else f"Ação: {a}",
                            key="aud_acao", label_visibility="collapsed", width=260)
        resultado = st.selectbox("Resultado", [None] + list(RESULTADOS), format_func=lambda r: "Resultado: todos" if r is None else f"Resultado: {RESULTADOS[r]}",
                                 key="aud_resultado", label_visibility="collapsed", width=190)
        quem = st.selectbox("Usuário", [None] + list(pessoas), format_func=lambda u: "Usuário: todos" if u is None else f"Usuário: {pessoas[u]}",
                            key="aud_usuario", label_visibility="collapsed", width=230)
        st.space("stretch")
        st.selectbox("Período", list(PERIODOS), index=list(PERIODOS).index(dias) if dias in PERIODOS else 1, format_func=PERIODOS.get,
                     key="aud_dias", label_visibility="collapsed", width=170)

    filtros = {"dias": dias, "recurso": recurso, "acao": acao, "resultado": resultado, "user_id": quem}
    if any(v is not None for k, v in filtros.items() if k != "dias"):
        try:
            dados = _carregar(token, filtros)
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
    else:
        dados = base
    itens = linhas(dados.get("eventos"), usuarios)
    if len(itens) >= (dados.get("limite") or 300):
        st.html(f'<p class="crh-meta">Mostrando os {len(itens)} eventos mais recentes. Use os filtros ou um período menor para achar um evento mais antigo.</p>')
    _tabela(itens)

    alvo = st.session_state.get("aud_detalhe")
    if alvo is not None:
        linha = next((l for l in itens if l["id"] == alvo), None)
        _modal_detalhe(linha) if linha else _fechar()
