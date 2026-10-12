"""
Página "Ausências" do RH e do Admin (Figma 243:846; modais 243:1127 "Rejeitar ausência" e 243:1153
"Registrar ausência"; parte das tarefas 20 e 24 da change concluir-frontend-streamlit).

Abas Pendentes (Rejeitar com justificativa, Aprovar), Aprovadas (Registrar), Registradas e Rejeitadas,
com filtros de tipo e departamento. Endpoints: `ausencias?status=...`, `ausencias/{id}/aprovar|rejeitar|
registrar`, `ausencias/{id}/comprovante` (link temporário, auditado) e `organograma`. Só RH e Admin; o
backend confere, bloqueia quem decide a própria ausência e recusa diagnóstico ou CID na observação.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (
    ApiError,
    abrir_comprovante_ausencia,
    aprovar_ausencia,
    ausencias_rh,
    organograma,
    registrar_ausencia_aprovada,
    rejeitar_ausencia,
)
from decisoes_modelo import ABAS_AUSENCIAS, linhas_ausencias, pessoas, resumo_ausencias, tipos_ausencia_presentes, validar_motivo
from ponto_modelo import TIPOS_AUSENCIA
from theme import alerta, render_hero, render_indicadores, render_topbar

_CACHE = "ausencias_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'por_status': {status: [ausências]}, 'organograma'} guardado por 20 s. Erro de uma lista sobe."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"por_status": {s: ausencias_rh(token, s).get("ausencias") or [] for s in ABAS_AUSENCIAS.values()}}
    try:
        dados["organograma"] = organograma(token)
    except ApiError:
        dados["organograma"] = {}
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("modal_ausencia", None)


def _concluir(aviso: str) -> None:
    st.session_state.pop(_CACHE, None)
    _fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _campos(linhas: list[tuple[str, str]], destaque: str | None = None) -> None:
    cor = ' style="color:#D97706"'
    campos = "".join(f'<p class="r">{html.escape(r)}</p><p class="v"{cor if r == destaque else ""}>{html.escape(v)}</p>' for r, v in linhas)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos}</div>')


@st.dialog("Rejeitar ausência", width="small", on_dismiss=_fechar)
def _modal_rejeitar(linha: dict) -> None:
    _campos([("Pessoa", linha["pessoa"]), ("Tipo", linha["tipo"]), ("Data", linha["periodo"])])
    texto = st.text_area("Justificativa (obrigatória)", max_chars=1000, key="aus_rej_texto", height=90, help="Não escreva diagnóstico nem código CID.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="aus_rej_voltar"):
            _fechar()
            st.rerun()
        if st.button("Rejeitar ausência", type="primary", key="aus_rej_ok"):
            erro_campo = validar_motivo(texto)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                rejeitar_ausencia(st.session_state.token, linha["id"], texto.strip())
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            st.session_state.pop("aus_rej_texto", None)
            _concluir(f"Ausência de {linha['pessoa']} rejeitada. A pessoa vê a justificativa.")


@st.dialog("Registrar ausência", width="small", on_dismiss=_fechar)
def _modal_registrar(linha: dict) -> None:
    _campos([("Pessoa", linha["pessoa"]), ("Tipo", linha["tipo"]), ("Data", linha["periodo"]), ("Aprovada em", linha["aprovada_em"])], destaque="Aprovada em")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="aus_reg_voltar"):
            _fechar()
            st.rerun()
        if st.button("Registrar", type="primary", key="aus_reg_ok"):
            try:
                registrar_ausencia_aprovada(st.session_state.token, linha["id"])
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _concluir(f"Ausência de {linha['pessoa']} registrada.")


def _abrir_comprovante(ausencia_id: int) -> None:
    try:
        st.session_state.aus_link = abrir_comprovante_ausencia(st.session_state.token, ausencia_id).get("comprovante_url")
        st.session_state.pop("aus_erro", None)
    except ApiError as erro:
        st.session_state.aus_erro = erro.message
        st.session_state.pop("aus_link", None)
    st.rerun()


def _tabela(linhas: list[dict], status: str, token: str) -> None:
    pesos = [2.4, 1.3, 1.9, 3, 1.2, 1.8]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Tipo", "Período", "Motivo", "Comprovante", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhuma ausência nesta aba.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_linf_{i}" if status in ("Pendente", "Aprovada") else f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["pessoa"])}</p><p class="d">{html.escape(l["detalhe"])}</p></div>')
                c[1].html(f'<span class="crh-selo {l["selo_tipo"]}">{html.escape(l["tipo"])}</span>', width="content")
                c[2].html(f'<p class="crh-doc-prazo">{html.escape(l["periodo"])}</p>')
                c[3].html(f'<p class="crh-doc-prazo">{html.escape(l["motivo"])}</p>')
                with c[4]:
                    if not l["comprovante"]:
                        st.html('<p class="crh-doc-prazo">—</p>')
                    elif st.button("Ver", type="tertiary", key=f"rh_abrir_aus_{l['id']}"):
                        _abrir_comprovante(l["id"])
                with c[5]:
                    if status not in ("Pendente", "Aprovada"):
                        continue
                    if l["proprio"]:
                        st.html('<p class="crh-meta">Sua: outra pessoa decide</p>')
                        continue
                    with st.container(horizontal=True, gap="small"):
                        if status == "Pendente":
                            if st.button("Rejeitar", type="tertiary", key=f"rh_recusar_aus_{l['id']}"):
                                st.session_state.modal_ausencia = ("rejeitar", l["id"])
                                st.rerun()
                            if st.button("Aprovar", type="tertiary", key=f"aus_aprovar_{l['id']}"):
                                try:
                                    aprovar_ausencia(token, l["id"])
                                except ApiError as erro:
                                    st.session_state.aus_erro = erro.message
                                    st.rerun()
                                _concluir(f"Ausência de {l['pessoa']} aprovada. Falta registrar.")
                        elif st.button("Registrar", type="tertiary", key=f"aus_registrar_{l['id']}"):
                            st.session_state.modal_ausencia = ("registrar", l["id"])
                            st.rerun()


def pagina_ausencias() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Ausências", "Atestados, faltas, afastamentos e licenças enviados pelos colaboradores")

    # O menu já esconde a tela, mas o endereço pode ser aberto direto.
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return

    with st.spinner("Carregando..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        alerta(st.empty(), "erro", erro.message)
        return

    por_status = dados["por_status"]
    numeros = resumo_ausencias(por_status, date.today())
    render_indicadores([
        ("Pendentes", str(numeros["pendentes"]), "ambar"),
        ("Aprovadas, falta registrar", str(numeros["aprovadas"]), "azul"),
        ("Registradas no mês", str(numeros["registradas_mes"]), "verde"),
        ("Rejeitadas no mês", str(numeros["rejeitadas_mes"]), ""),
    ])

    org = dados["organograma"]
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    todas = [a for lista in por_status.values() for a in lista]
    with st.container(horizontal=True, vertical_alignment="center", key="rh_barra"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(ABAS_AUSENCIAS), default="Pendentes", required=True, key="aus_aba", label_visibility="collapsed")
        st.space("stretch")
        tipo = st.selectbox("Tipo", [None] + tipos_ausencia_presentes(todas), format_func=lambda t: "Tipo: Todos" if t is None else f"Tipo: {TIPOS_AUSENCIA.get(t, t)}", key="aus_tipo", label_visibility="collapsed", width=180)
        dep = st.selectbox("Departamento", [None] + sorted(deps, key=deps.get), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}", key="aus_dep", label_visibility="collapsed", width=230)

    if link := st.session_state.get("aus_link"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<p class="crh-meta">Link do comprovante pronto.</p>', width="content")
            st.link_button("Abrir comprovante", link)
    if erro_acao := st.session_state.pop("aus_erro", None):
        alerta(st.empty(), "erro", erro_acao)

    status = ABAS_AUSENCIAS[aba]
    mapa = pessoas(org)
    meu = usuario.get("colaborador_id")
    _tabela(linhas_ausencias(por_status[status], mapa, meu, tipo, dep), status, token)

    modal = st.session_state.get("modal_ausencia")
    if not modal:
        return
    acao, aus_id = modal
    origem = "Pendente" if acao == "rejeitar" else "Aprovada"
    linha = next((l for l in linhas_ausencias(por_status[origem], mapa, meu) if l["id"] == aus_id and not l["proprio"]), None)
    if linha is None:
        _fechar()  # a ausência mudou de situação desde que a linha foi desenhada
        return
    (_modal_rejeitar if acao == "rejeitar" else _modal_registrar)(linha)
