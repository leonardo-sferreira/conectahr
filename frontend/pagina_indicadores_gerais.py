"""
Página "Indicadores gerais" do grupo Admin (F33, Figma 249:7492; tarefa 49 da change concluir-frontend-streamlit).
RH e Admin, como o backend.

Quatro números (headcount, turnover, absenteísmo e eNPS), admissões e desligamentos por trimestre, headcount por
departamento, horas extras do período, filtro de período e "Exportar CSV" (auditado no backend). Endpoints:
`indicadores` GET e `indicadores/exportar_csv` GET.

Diferenças do Figma, por falta de dado no backend:
- o eNPS aparece como "—", porque não há pesquisa de eNPS;
- não há filtro por departamento, porque o cálculo é da empresa toda;
- não há "Departamento com mais horas".
Abaixo do mínimo de pessoas do backend, os totais aparecem como "Oculto".
"""

import time
from datetime import date

import streamlit as st

import indicadores_gerais_modelo as im
from api_client import ApiError, exportar_indicadores_csv, indicadores_gerais
from theme import alerta, render_barras_indicadores, render_hero, render_horas_mensais, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 60


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def pagina_indicadores_gerais() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    meses = st.session_state.get("ig_meses", 12)
    render_hero("Indicadores gerais", f"Toda a empresa · últimos {meses} meses")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    hoje = date.today()
    inicio, fim = im.periodo(meses, hoje)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        st.selectbox("Período", list(im.PERIODOS), index=list(im.PERIODOS).index(12), format_func=lambda m: f"Período: {im.PERIODOS[m]}",
                     key="ig_meses", label_visibility="collapsed", width=200)
        if st.button("Exportar CSV", key="ig_exportar"):
            try:
                st.session_state.ig_csv = exportar_indicadores_csv(token, inicio, fim).get("csv") or ""
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
        if st.session_state.get("ig_csv") is not None:
            st.download_button("Baixar CSV", st.session_state.ig_csv.encode("utf-8"), file_name=f"indicadores_{inicio}_{fim}.csv", mime="text/csv",
                               key="ig_baixar", type="primary")
    try:
        with st.spinner("Calculando..."):
            ind = _guardado(f"ig_cache_{inicio}_{fim}", lambda: indicadores_gerais(token, inicio, fim))
            por_trimestre = [(r, _guardado(f"ig_cache_{a}_{b}", lambda a=a, b=b: indicadores_gerais(token, a, b))) for r, a, b in im.trimestres(hoje)]
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    render_indicadores(im.cartoes(ind, meses))
    if ind.get("totais_omitidos"):
        st.html(f'<p class="crh-meta">Totais ocultos: a empresa tem menos de {ind.get("minimo_pessoas") or 5} pessoas, '
                "e o número poderia identificar alguém.</p>")
    esquerda, direita = st.columns(2)
    with esquerda:
        render_horas_mensais(im.serie_trimestres(por_trimestre), titulo="Admissões e desligamentos por trimestre")
    with direita:
        render_barras_indicadores("Headcount por departamento", im.distribuicao(ind), "Oculto: menos pessoas que o mínimo para mostrar.")
        st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Horas extras</p>'
                f'<div class="crh-lgpd-resumo" style="background:transparent;padding:0"><div><span>Total no período</span>'
                f'<b class="ambar">{im.horas_extras(ind)}</b></div></div></div>')
    st.html('<p class="crh-meta">eNPS: ainda não há pesquisa de eNPS no sistema. Os números são da empresa toda, sem dados de pessoas.</p>')
