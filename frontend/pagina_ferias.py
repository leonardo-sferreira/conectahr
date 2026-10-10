"""
Página "Férias" (Figma 40:22; modal 221:230; fluxo F07; tarefas 22 a 25 da change
concluir-frontend-streamlit).

- Dois cartões: o limite de dias por pedido e o fracionamento (períodos usados de quantos o contrato
  permite), vindos de `minha_situacao_ferias`, com a data do próximo período aquisitivo.
- "Solicitar férias" (`ferias/solicitacoes`): início, fim, observação para o gestor; o quadro mostra os
  dias pedidos, o limite e qual período é. A tela avisa antes de enviar, e o backend confere de novo.
- Histórico (`minhas_ferias`), com "Cancelar" no pedido pendente (`ferias/{id}/cancelar`).

Tudo é do próprio colaborador. Quem decide é o gestor ou o RH, em outra tela; ninguém decide o próprio
pedido (regra do backend).

Diferenças em relação ao Figma: o primeiro cartão mostra "Até N dias" por pedido, e não "Dias
disponíveis", porque o backend não tem saldo de férias (tarefa 74); "Ver calendário" leva à tela
Calendário, que ainda não existe (tarefa 56).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, cancelar_ferias, minha_situacao_ferias, minhas_ferias, solicitar_ferias
from ferias_modelo import dias_do_periodo, historico, regras_do_pedido, resumo, resumo_do_pedido, validar_pedido
from theme import alerta, render_hero, render_topbar

_CACHE = "ferias_cache"
_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    """{'ferias', 'situacao'} por 20 s. Erro do histórico sobe (404 = sem colaborador); sem a situação, a
    tela segue sem os cartões."""
    cache = st.session_state.get(_CACHE)
    if cache and time.time() - cache["em"] < _VALIDADE_CACHE_S:
        return cache["dados"]
    dados = {"ferias": minhas_ferias(token).get("ferias") or []}
    try:
        dados["situacao"] = minha_situacao_ferias(token)
    except ApiError:
        dados["situacao"] = None
    st.session_state[_CACHE] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    st.session_state.pop(_CACHE, None)


def _fechar() -> None:
    st.session_state.pop("modal_ferias", None)


@st.dialog("Solicitar férias", width="small", on_dismiss=_fechar)
def _modal_solicitar(situacao: dict) -> None:
    hoje = date.today()
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Início", value=None, min_value=hoje, format="DD/MM/YYYY", key="fe_inicio")
    fim = c2.date_input("Fim", value=None, min_value=hoje, format="DD/MM/YYYY", key="fe_fim")
    linhas = resumo_do_pedido(situacao, inicio, fim)
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        + "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in linhas)
        + "</div>"
    )
    observacao = st.text_input("Observação para o gestor (opcional)", max_chars=500, key="fe_obs")
    st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(regras_do_pedido(situacao))}</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="fe_cancelar_modal"):
            _fechar()
            st.rerun()
        if st.button("Enviar para o gestor", type="primary", key="fe_enviar"):
            erro_campo = validar_pedido(situacao, inicio, fim, hoje, observacao)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                solicitar_ferias(st.session_state.token, inicio.isoformat(), fim.isoformat(), dias_do_periodo(inicio, fim), observacao.strip() or None)
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("fe_inicio", "fe_fim", "fe_obs"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Pedido de férias enviado. Seu gestor ou o RH decide."
            st.rerun()


def _cancelar(ferias_id: int) -> None:
    try:
        cancelar_ferias(st.session_state.token, ferias_id)
        st.session_state.aviso_toast = "Pedido de férias cancelado."
    except ApiError as erro:
        st.session_state.ferias_erro = erro.message
    _invalidar()
    st.rerun()


def pagina_ferias() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Férias", "Solicite e acompanhe seus períodos de descanso")

    with st.spinner("Carregando suas férias..."):
        try:
            dados, erro = _carregar(token), None
        except ApiError as falha:
            dados, erro = None, falha
    if erro is not None:
        if erro.status_code == 404:
            st.html(
                '<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Sem cadastro de colaborador</p>'
                '<p class="crh-meta">Sua conta não tem cadastro de colaborador, então não há férias para pedir.</p></div>'
            )
        else:
            alerta(st.empty(), "erro", erro.message)
        return
    if erro_cancelar := st.session_state.pop("ferias_erro", None):
        alerta(st.empty(), "erro", erro_cancelar)

    situacao = dados["situacao"]
    numeros = resumo(situacao, date.today()) if situacao else None
    with st.container(horizontal=True, vertical_alignment="center", key="ferias_topo"):
        if numeros:
            st.html(
                f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">Dias por pedido</p><p class="crh-stat-valor">{html.escape(numeros["limite"])}</p></div>'
                f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">{html.escape(numeros["fracionamento_rotulo"])}</p>'
                f'<p class="crh-stat-valor">{html.escape(numeros["fracionamento"])}</p></div>',
                width="stretch",
            )
        else:
            st.html('<div class="crh-painel crh-stat"><p class="crh-meta">Não foi possível carregar a situação das suas férias agora.</p></div>', width="stretch")
        if st.button("Ver calendário", key="fe_calendario"):
            st.toast("A tela Calendário ainda está em construção.")
        if st.button("Solicitar férias", type="primary", key="fe_solicitar", disabled=not (numeros and numeros["pode_pedir"])):
            st.session_state.modal_ferias = True
            st.rerun()
    if numeros and numeros["nota"]:
        st.html(f'<p class="crh-meta">{html.escape(numeros["nota"])}</p>')
    if numeros and numeros["motivo_bloqueio"]:
        st.html(f'<p class="crh-nota-ambar">{html.escape(numeros["motivo_bloqueio"])}</p>')

    st.html('<p class="crh-bloco-titulo">Histórico de solicitações</p>')
    linhas = historico(dados["ferias"])
    if not linhas:
        st.html('<p class="crh-meta">Você ainda não pediu férias.</p>')
    else:
        with st.container(key="ferias_historico"):
            for i, l in enumerate(linhas):
                with st.container(horizontal=True, vertical_alignment="center", key=f"ferias_lin_{i}"):
                    st.html(
                        f'<div class="crh-fe-item"><span class="p {l["tipo"]}"></span><div><p class="t">{html.escape(l["titulo"])}</p>'
                        f'<p class="d">{html.escape(l["detalhe"])}</p></div></div>',
                        width="stretch",
                    )
                    st.html(f'<span class="crh-selo {l["tipo"]}">{html.escape(l["badge"])}</span>', width="content")
                    if l["cancelavel"] and st.button("Cancelar", type="tertiary", key=f"fe_cancelar_{l['id']}"):
                        _cancelar(l["id"])

    if st.session_state.get("modal_ferias") and situacao:
        _modal_solicitar(situacao)
