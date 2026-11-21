"""
Página "Calendário" (Figma 233:2394; tarefa 56 da change concluir-frontend-streamlit). Qualquer perfil; abre pelo
"Calendário →" da tela Férias e o menu fica em "Férias".

Mês com ‹ e ›, feriados e férias aprovadas (do departamento, ou de todos para RH e Admin), "Mostrar férias" para ver só
os feriados, "Próximos eventos" e a legenda. Endpoint: `calendario` GET, que agora devolve as férias só com nome,
período e status.

Diferença do Figma: não há "Prazo" (autoavaliação, fechamento do ponto), porque o backend não junta esses prazos num
lugar; os prazos de cada pessoa ficam na Central de Pendências.
"""

import html
import time
from datetime import date

import streamlit as st

import calendario_modelo as cm
from api_client import ApiError, calendario
from delegacoes_modelo import hoje_brasilia
from theme import alerta, render_hero, render_topbar

_VALIDADE_CACHE_S = 120


def _carregar(token: str) -> dict:
    item = st.session_state.get("cal_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = calendario(token)
    st.session_state.cal_cache = {"em": time.time(), "dados": dados}
    return dados


def _tabela(semanas: list[list[dict | None]]) -> str:
    cab = "".join(f"<th>{d}</th>" for d in cm.SEMANA)
    linhas = []
    for semana in semanas:
        celulas = []
        for dia in semana:
            if dia is None:
                celulas.append('<td class="fora"></td>')
                continue
            classes = " ".join(c for c, ok in (("fds", dia["fds"]), ("hoje", dia["hoje"])) if ok)
            marcas = "".join(f'<span class="tag {tipo}" title="{html.escape(texto)}">{html.escape(texto)}</span>' for texto, tipo in dia["marcas"])
            celulas.append(f'<td class="{classes}"><span class="n">{dia["dia"]}</span>{marcas}</td>')
        linhas.append(f"<tr>{''.join(celulas)}</tr>")
    return f'<div class="crh-cal"><table><thead><tr>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'


def pagina_calendario() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    render_hero("Calendário", "Feriados e férias da equipe")
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    hoje = hoje_brasilia()
    ano, mes = st.session_state.get("cal_mes") or (hoje.year, hoje.month)
    feriados, ferias = dados.get("feriados") or [], dados.get("ferias") or []
    esquerda, direita = st.columns([2.2, 1], gap="medium")
    with esquerda:
        with st.container(key="ferias_calendario"):
            with st.container(horizontal=True, vertical_alignment="center"):
                if st.button("‹", key="cal_anterior", help="Mês anterior"):
                    st.session_state.cal_mes = cm.mes_vizinho(ano, mes, -1)
                    st.rerun()
                st.html(f'<p class="crh-cal-titulo">{cm.MESES[mes - 1]} de {ano}</p>', width="content")
                if st.button("›", key="cal_seguinte", help="Mês seguinte"):
                    st.session_state.cal_mes = cm.mes_vizinho(ano, mes, 1)
                    st.rerun()
                st.space("stretch")
                if (ano, mes) != (hoje.year, hoje.month) and st.button("Hoje", key="cal_hoje", type="tertiary"):
                    st.session_state.pop("cal_mes", None)
                    st.rerun()
                mostrar = st.checkbox("Mostrar férias da equipe", value=True, key="cal_mostrar_ferias")
            st.html(_tabela(cm.semanas(ano, mes, feriados, ferias, hoje, mostrar)))
    with direita:
        eventos = cm.proximos(feriados, ferias, hoje, mostrar_ferias=mostrar)
        itens = "".join(f'<div class="crh-rd-item crh-cal-ev"><span class="ponto {e["tipo"]}"></span>'
                        f'<div class="txt"><p class="t">{html.escape(e["titulo"])}</p><p class="d">{html.escape(e["quando"])}</p></div></div>' for e in eventos)
        st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Próximos eventos</p>'
                + (itens or '<p class="crh-meta">Nenhum feriado ou férias pela frente.</p>') + "</div>")
        st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Legenda</p><div class="crh-cal-legenda">'
                '<span class="crh-selo err">Feriado</span><span class="crh-selo amb">Ponto facultativo</span><span class="crh-selo azul">Férias</span></div>'
                f'<p class="crh-meta" style="margin-top:8px">{html.escape(cm.nota_escopo(usuario.get("perfil", "")))}</p></div>')
