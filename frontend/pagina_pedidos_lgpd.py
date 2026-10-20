"""
Página "Pedidos LGPD" do grupo RH (Figma 249:5709 e o modal 249:5955; change pedidos-lgpd). Só RH e Admin.

Indicadores (abertos, vencendo em 3 dias, respondidos no ano), abas "Abertos" e "Respondidos", filtro de tipo e a
tabela com pessoa, pedido, abertura, prazo (15 dias, LGPD art. 19) e "Responder →". O modal mostra pessoa, pedido,
prazo e o detalhe escrito pelo titular, e pede a decisão (atendido, atendido em parte ou não atendido) e a resposta
ao titular. Ninguém responde o próprio pedido (o backend recusa e audita). Nos respondidos, "Ver" mostra a resposta.
Endpoints: `solicitacoes` GET (só os `privacidade_lgpd`), `organograma` (nomes) e `solicitacoes/{id}/atender` ou
`indeferir`.
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, atender_solicitacao, indeferir_solicitacao, organograma, solicitacoes_rh
from campos import campo
from decisoes_modelo import pessoas
from pedidos_lgpd_modelo import ABAS, DECISOES, do_lgpd, indicadores, linhas, validar_resposta
from privacidade_modelo import SUBTIPOS
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    item = st.session_state.get("lgpd_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = {"solicitacoes": do_lgpd(solicitacoes_rh(token).get("solicitacoes") or [])}
    try:
        dados["pessoas"] = pessoas(organograma(token))
    except ApiError:
        dados["pessoas"] = {}
    st.session_state.lgpd_cache = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    st.session_state.pop("lgpd_modal", None)


def _concluir(aviso: str) -> None:
    for chave in [k for k in st.session_state if str(k).startswith("lgpd_") and k not in ("lgpd_aba", "lgpd_tipo")]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _resumo(linha: dict, prazo_ou_decisao: str) -> str:
    return (f'<div class="crh-lgpd-resumo"><div><span>Pessoa</span><b>{html.escape(linha["nome"])}</b></div>'
            f'<div><span>Pedido</span><b>{html.escape(linha["pedido"].split(" — ")[0])}</b></div>{prazo_ou_decisao}</div>')


@st.dialog("Responder pedido LGPD", width="medium", on_dismiss=_fechar)
def _modal_responder(linha: dict, pedido: dict) -> None:
    prazo = f'<div><span>Prazo</span><b class="ambar">{html.escape(linha["prazo"][0].replace("até ", ""))}</b></div>'
    st.html(_resumo(linha, prazo) + f'<p class="crh-meta">Pedido do titular</p><p class="crh-lgpd-detalhe">{html.escape(pedido.get("descricao") or "")}</p>')
    decisao = st.radio("Decisão", list(DECISOES), format_func=DECISOES.get, index=None, key="lgpd_decisao")
    resposta = campo(st, "Resposta ao titular", "texto", "lgpd_resposta", area=True, max_chars=1000, height=100,
                     placeholder="O que foi feito, ou por que não foi possível. A pessoa vê esta resposta.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="lgpd_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Enviar resposta", type="primary", key="lgpd_enviar"):
            erro = validar_resposta(decisao, resposta)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                if decisao == "nao_atendido":
                    indeferir_solicitacao(st.session_state.token, linha["id"], resposta.strip())
                else:
                    atender_solicitacao(st.session_state.token, linha["id"], resposta.strip(), parcial=decisao == "atendido_parcial")
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Resposta enviada ao titular.")


@st.dialog("Pedido LGPD", width="medium", on_dismiss=_fechar)
def _modal_ver(linha: dict, pedido: dict) -> None:
    selo, tom = linha["resultado"]
    decisao = f'<div><span>Decisão</span><b><span class="crh-selo {tom}">{html.escape(selo)}</span></b></div>'
    st.html(_resumo(linha, decisao)
            + f'<p class="crh-meta">Pedido do titular</p><p class="crh-lgpd-detalhe">{html.escape(pedido.get("descricao") or "")}</p>'
            + f'<p class="crh-meta">Resposta ao titular · {html.escape(linha["respondido_em"])}</p>'
            + f'<p class="crh-lgpd-detalhe">{html.escape(pedido.get("justificativa_decisao") or "—")}</p>')


def _tabela(itens: list[dict], aba: str, meu_colaborador_id) -> None:
    pesos = [2.2, 3.2, 1.3, 1.3, 1.3]
    cab = ["Pessoa", "Pedido", "Aberto em", "Prazo" if aba == "Abertos" else "Decisão", ""]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), cab):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not itens:
            with st.container(key="rh_lin_vazio"):
                st.html(f'<p class="crh-meta">{"Nenhum pedido aberto." if aba == "Abertos" else "Nenhum pedido respondido ainda."}</p>')
        for i, l in enumerate(itens):
            with st.container(key=f"rh_lin_{i}" + ("_alerta" if l["destaque"] and aba == "Abertos" else "")):
                col = st.columns(pesos, vertical_alignment="center")
                dep = f'<p class="d">{html.escape(l["departamento"])}</p>' if l["departamento"] else ""
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["nome"])}</p>{dep}</div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(l["pedido"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["aberto_em"])}</p>')
                selo, tom = l["prazo"] if aba == "Abertos" else l["resultado"]
                col[3].html(f'<span class="crh-selo {tom}">{html.escape(selo)}</span>', width="content")
                with col[4]:
                    if aba == "Abertos":
                        proprio = l["colaborador_id"] == meu_colaborador_id
                        if st.button("Responder →", type="tertiary", key=f"lgpd_resp_{l['id']}", disabled=proprio,
                                     help="Outra pessoa do RH responde o seu pedido." if proprio else None):
                            st.session_state.lgpd_modal = ("responder", l["id"])
                            st.rerun()
                    elif st.button("Ver", type="tertiary", key=f"lgpd_ver_{l['id']}"):
                        st.session_state.lgpd_modal = ("ver", l["id"])
                        st.rerun()


def pagina_pedidos_lgpd() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Pedidos LGPD", "Pedidos dos colaboradores sobre os próprios dados · prazo de 15 dias")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    hoje = date.today()
    lgpd = dados["solicitacoes"]
    render_indicadores(indicadores(lgpd, hoje))
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(ABAS), default="Abertos", required=True, key="lgpd_aba", label_visibility="collapsed")
        st.space("stretch")
        subtipo = st.selectbox("Tipo", [None] + list(SUBTIPOS), format_func=lambda s: "Tipo: Todos" if s is None else f"Tipo: {SUBTIPOS[s]}",
                               key="lgpd_tipo", label_visibility="collapsed", width=300)
    itens = linhas(lgpd, dados["pessoas"], aba, hoje, subtipo)
    _tabela(itens, aba, usuario.get("colaborador_id"))
    st.html('<p class="crh-meta">Todo pedido e resposta ficam na auditoria. O encarregado (DPO) acompanha esta fila.</p>')

    modal = st.session_state.get("lgpd_modal")
    if not modal:
        return
    tipo, alvo = modal
    pedido = next((s for s in lgpd if s["id"] == alvo), None)
    linha = next((l for l in linhas(lgpd, dados["pessoas"], "Abertos" if tipo == "responder" else "Respondidos", hoje) if l["id"] == alvo), None)
    if not pedido or not linha:
        _fechar()
    elif tipo == "responder":
        _modal_responder(linha, pedido)
    else:
        _modal_ver(linha, pedido)
