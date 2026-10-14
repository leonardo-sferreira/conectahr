"""
Página "Férias" (Figma 40:22; modal 221:230; fluxo F07; tarefas 22 a 25 da change
concluir-frontend-streamlit).

- Três cartões (change ponto-rep-p-e-ferias-clt, tarefas 6.2 e 6.3): o saldo do período aquisitivo, os períodos
  usados de quantos o contrato permite e os dias vendidos, vindos de `minha_situacao_ferias`, com até quando tirar.
- "Solicitar férias" (`ferias/solicitacoes`): início, fim, os dias a vender (até 10, uma vez por período aquisitivo)
  e a observação para o gestor; o quadro mostra os dias, o saldo agora e o que sobra. A tela avisa antes de enviar
  com as mesmas regras do backend, que confere de novo.
- Histórico (`minhas_ferias`), com "Cancelar" no pedido pendente (`ferias/{id}/cancelar`).

Tudo é do próprio colaborador. Quem decide é o gestor ou o RH, em outra tela; ninguém decide o próprio
pedido (regra do backend).

"Ver calendário" abre o calendário do mês (Figma 466:833; change ponto-rep-p-e-ferias-clt, tarefa 7.3): feriados
e pontos facultativos (`calendario`, com os nacionais importados da BrasilAPI pelo RH) e as suas férias aprovadas
ou em análise. Diferença em relação ao Figma: o calendário fica abaixo dos cartões, e o pedido continua no modal;
a legenda troca "Período escolhido" por "Pedido em análise".
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, calendario, cancelar_ferias, minha_situacao_ferias, minhas_ferias, solicitar_ferias
from ferias_modelo import (
    LEGENDA_CALENDARIO,
    NOTA_CALENDARIO,
    SEMANA_CALENDARIO,
    calendario_mes,
    dias_do_periodo,
    historico,
    mes_vizinho,
    primeiro_inicio,
    regras_do_pedido,
    resumo,
    resumo_do_pedido,
    validar_pedido,
)
from pagamento_modelo import MESES
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
        dados["situacao"], dados["situacao_erro"] = minha_situacao_ferias(token), None
    except ApiError as erro:
        # A mensagem do backend vai para a tela: "não foi possível" sozinho escondia o motivo.
        dados["situacao"], dados["situacao_erro"] = None, erro.message
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
    # O calendário abre no primeiro dia permitido (hoje + antecedência, de `minha_situacao_ferias`); o fim, a partir do início.
    primeiro = primeiro_inicio(situacao, hoje)
    inicio = c1.date_input("Início", value=None, min_value=primeiro, max_value=date(hoje.year + 2, 12, 31), format="DD/MM/YYYY", key="fe_inicio",
                           help=f"A partir de {primeiro.strftime('%d/%m/%Y')}: férias são pedidas com antecedência.")
    fim = c2.date_input("Fim", value=None, min_value=inicio or primeiro, max_value=date(hoje.year + 2, 12, 31), format="DD/MM/YYYY", key="fe_fim")
    linhas = resumo_do_pedido(situacao, inicio, fim, int(st.session_state.get("fe_abono") or 0))
    st.html(
        '<div class="crh-campos crh-campos-direita">'
        + "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in linhas)
        + "</div>"
    )
    abono = 0
    if situacao.get("pode_vender"):
        abono = st.number_input("Vender dias (opcional)", min_value=0, max_value=int(situacao.get("maximo_abono") or 10), value=0, step=1, key="fe_abono",
                                help="Abono pecuniário: você recebe em dinheiro os dias vendidos, que saem do saldo. Uma vez por período aquisitivo.")
    observacao = st.text_input("Observação para o gestor (opcional)", max_chars=500, key="fe_obs")
    st.html(f'<div class="crh-incluso"><p class="n" style="margin:0">{html.escape(regras_do_pedido(situacao))}</p></div>')
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="fe_cancelar_modal"):
            _fechar()
            st.rerun()
        if st.button("Enviar para o gestor", type="primary", key="fe_enviar"):
            erro_campo = validar_pedido(situacao, inicio, fim, hoje, observacao, int(abono), _feriados(st.session_state.token)[0])
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                return
            try:
                solicitar_ferias(st.session_state.token, inicio.isoformat(), fim.isoformat(), dias_do_periodo(inicio, fim), observacao.strip() or None, int(abono))
            except ApiError as erro:
                alerta(slot, "erro", erro.message)
                return
            _invalidar()
            _fechar()
            for chave in ("fe_inicio", "fe_fim", "fe_obs", "fe_abono"):
                st.session_state.pop(chave, None)
            st.session_state.aviso_toast = "Pedido de férias enviado. Seu gestor ou o RH decide."
            st.rerun()


def _feriados(token: str) -> tuple[list[dict], str | None]:
    """Os feriados de `calendario`, guardados na sessão (são os mesmos para todos e mudam pouco)."""
    if "fe_feriados" not in st.session_state:
        try:
            st.session_state.fe_feriados = calendario(token).get("feriados") or []
        except ApiError as erro:
            return [], erro.message
    return st.session_state.fe_feriados, None


def _html_calendario(semanas: list[list[dict | None]]) -> str:
    cab = "".join(f"<th>{d}</th>" for d in SEMANA_CALENDARIO)
    linhas = []
    for semana in semanas:
        celulas = []
        for dia in semana:
            if dia is None:
                celulas.append('<td class="fora"></td>')
                continue
            classes = " ".join(c for c, ok in (("fds", dia["fds"]), ("hoje", dia["hoje"]), ("ferias", dia["ferias"] == "aprovada"),
                                                ("analise", dia["ferias"] == "pendente")) if ok)
            marcas = "".join(f'<span class="tag {tipo}" title="{html.escape(nome)}">{html.escape(texto)}</span>' for texto, tipo, nome in dia["marcas"])
            celulas.append(f'<td class="{classes}"><span class="n">{dia["dia"]}</span>{marcas}</td>')
        linhas.append(f"<tr>{''.join(celulas)}</tr>")
    return f'<div class="crh-cal"><table><thead><tr>{cab}</tr></thead><tbody>{"".join(linhas)}</tbody></table></div>'


def _calendario(token: str, ferias: list[dict]) -> None:
    """Calendário do mês (Figma 466:833), com ‹ e › para trocar de mês."""
    hoje = date.today()
    ano, mes = st.session_state.get("fe_cal_mes") or (hoje.year, hoje.month)
    feriados, erro = _feriados(token)
    with st.container(key="ferias_calendario"):
        with st.container(horizontal=True, vertical_alignment="center"):
            if st.button("‹", key="fe_cal_anterior", help="Mês anterior"):
                st.session_state.fe_cal_mes = mes_vizinho(ano, mes, -1)
                st.rerun()
            st.html(f'<p class="crh-cal-titulo">{MESES[mes - 1]} de {ano}</p>', width="content")
            if st.button("›", key="fe_cal_seguinte", help="Mês seguinte"):
                st.session_state.fe_cal_mes = mes_vizinho(ano, mes, 1)
                st.rerun()
        if erro:
            alerta(st.empty(), "atencao", f"Os feriados não carregaram agora: {erro}")
        st.html(_html_calendario(calendario_mes(ano, mes, feriados, ferias, hoje)))
        st.html('<div class="crh-cal-legenda">' + "".join(f'<span class="crh-selo {tom}">{html.escape(t)}</span>' for t, tom in LEGENDA_CALENDARIO)
                + f'</div><p class="crh-meta" style="margin-top:8px">{html.escape(NOTA_CALENDARIO)}</p>')


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
                f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">Saldo de férias</p><p class="crh-stat-valor">{html.escape(numeros["saldo"])}</p></div>'
                f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">{html.escape(numeros["fracionamento_rotulo"])}</p>'
                f'<p class="crh-stat-valor">{html.escape(numeros["fracionamento"])}</p></div>'
                f'<div class="crh-painel crh-stat"><p class="crh-stat-rotulo">Dias vendidos</p><p class="crh-stat-valor">{html.escape(numeros["vendidos"])}</p></div>',
                width="stretch",
            )
        else:
            motivo = dados.get("situacao_erro") or ""
            st.html('<div class="crh-painel crh-stat"><p class="crh-meta">Não foi possível carregar a situação das suas férias agora'
                    f'{": " + html.escape(motivo) if motivo else "."}</p></div>', width="stretch")
        aberto = st.session_state.get("fe_cal_aberto", False)
        if st.button("Fechar calendário" if aberto else "Ver calendário", key="fe_calendario"):
            st.session_state.fe_cal_aberto = not aberto
            st.rerun()
        if st.button("Solicitar férias", type="primary", key="fe_solicitar", disabled=not (numeros and numeros["pode_pedir"])):
            st.session_state.modal_ferias = True
            st.rerun()
    for nota in (numeros or {}).get("notas") or []:
        st.html(f'<p class="crh-meta" style="margin:0">{html.escape(nota)}</p>')
    if numeros and numeros["motivo_bloqueio"]:
        st.html(f'<p class="crh-nota-ambar">{html.escape(numeros["motivo_bloqueio"])}</p>')

    if st.session_state.get("fe_cal_aberto"):
        _calendario(token, dados["ferias"])

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
