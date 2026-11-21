"""F18: indicadores do setor do Gestor (Figma 248:2694; change backend-gestor-pendencias, D2).

Os números vêm prontos de `indicadores_equipe` (só agregados do setor inteiro, sem pessoas; setor com menos de 5 pessoas
fica oculto). "Exportar CSV" chama `indicadores_equipe/exportar`, que grava a exportação na auditoria, e só então
oferece o arquivo. A folha individual continua em "Folha de ponto", com o escopo de sempre.
"""

import html
import time

import streamlit as st

from api_client import ApiError, exportar_indicadores_equipe, indicadores_equipe
from indicadores_equipe_modelo import PERIODO, ausencias_backend, cartoes_backend, csv_backend, serie_backend, texto_clima
from theme import alerta, render_barras_indicadores, render_hero, render_horas_mensais, render_indicadores, render_topbar

_CACHE = "ie_cache"
_VALIDADE_S = 60


def _nota(texto: str) -> None:
    st.html(f'<p class="crh-meta">{html.escape(texto)}</p>')


def invalidar() -> None:
    for chave in (_CACHE, "ie_csv_arquivo"):
        st.session_state.pop(chave, None)


def _carregar(token: str) -> dict:
    item = st.session_state.get(_CACHE)
    if item and item["token"] == token and time.time() - item["em"] < _VALIDADE_S:
        return item["dados"]
    dados = indicadores_equipe(token).get("indicadores") or {}
    st.session_state[_CACHE] = {"token": token, "em": time.time(), "dados": dados}
    return dados


def pagina_indicadores_equipe() -> None:
    usuario = st.session_state.usuario
    render_topbar(usuario.get("nome") or "")
    if str(usuario.get("perfil") or "").strip().upper() != "GESTOR":
        render_hero("Indicadores da equipe", "Acompanhe os dados do seu setor")
        with st.container(border=True):
            alerta(st.empty(), "erro", "Você não tem permissão para acessar esta tela.")
        return
    token = st.session_state.token
    try:
        with st.spinner("Carregando indicadores..."):
            ind = _carregar(token)
    except ApiError as erro:
        if erro.status_code != 401:
            render_hero("Indicadores da equipe", "Dados indisponíveis")
            with st.container(border=True):
                alerta(st.empty(), "erro", erro.message)
        return
    render_hero("Indicadores da equipe", f"{ind.get('setor') or 'Seu setor'} · últimos 6 meses")
    slot_csv = st.empty()
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        if st.button("Atualizar", type="tertiary", key="ie_atualizar"):
            invalidar()
            st.rerun()
        st.space("stretch")
        st.selectbox("Período", [PERIODO], key="ie_periodo", width=220, label_visibility="collapsed")
        if st.button("Exportar CSV", key="ie_csv", disabled=bool(ind.get("suprimido"))):
            try:
                exportado = exportar_indicadores_equipe(token).get("indicadores") or ind
            except ApiError as erro:
                alerta(slot_csv, "erro", erro.message)
            else:
                st.session_state.ie_csv_arquivo = csv_backend(exportado)
    if st.session_state.get("ie_csv_arquivo"):
        st.download_button("Baixar o CSV", st.session_state.ie_csv_arquivo, file_name="indicadores-do-setor.csv", mime="text/csv", key="ie_csv_baixar")
        _nota("A exportação ficou registrada na auditoria. O arquivo tem só números do setor, sem pessoas.")
    render_indicadores(cartoes_backend(ind))
    if ind.get("suprimido"):
        with st.container(border=True):
            alerta(st.empty(), "atencao", ind.get("motivo") or "Os números do setor estão ocultos.")
        return
    _nota(f"{ind.get('pessoas')} pessoas do setor, sem você e sem desligados. Absenteísmo: dias úteis cobertos por ausência aprovada ou "
          "registrada sobre os dias úteis do mês (segunda a sexta, sem feriados nacionais).")
    esquerda, direita = st.columns(2, gap="medium")
    with esquerda:
        render_horas_mensais(serie_backend(ind))
        _nota("Soma das horas extras registradas no ponto de cada mês; não indica fechamento do mês.")
    with direita:
        ausencias = ausencias_backend(ind)
        sem_ausencias = ausencias is not None and not any(n for _, n in ausencias)
        render_barras_indicadores("Ausências por mês", None if sem_ausencias else ausencias,
                                  "Nenhuma ausência aprovada ou registrada no período." if sem_ausencias else "")
        _nota("Ausências aprovadas ou registradas que tocam cada mês. Férias não entram.")
        st.html('<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Clima</p>'
                f'<p class="crh-meta">{html.escape(texto_clima(ind))}</p>'
                '<p class="crh-meta">O resultado do clima só aparece para grupos com 5 pessoas ou mais.</p></div>')
