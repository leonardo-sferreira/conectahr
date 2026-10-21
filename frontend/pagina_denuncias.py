"""
Página "Denúncias" da comissão de ética (Figma 540:1312 e os modais 544:1241 e 544:1269; change canal-de-denuncias).
Só para membros ativos da comissão, qualquer que seja o perfil: o menu mostra o item a quem é membro, e o backend
recusa os demais.

Indicadores (novas, em apuração, concluídas no ano), abas "Em aberto" e "Concluídas", filtro de tipo e a tabela com
protocolo, anônima ou identificada, tipo e começo do relato, data e situação (ou resultado). "Abrir →" mostra o relato,
quem se identificou, a conversa e "Mensagem ao denunciante" (a primeira passa a denúncia para em apuração); "Concluir
apuração" pede o resultado e o parecer final, que quem denunciou lê pelo código. Cada abertura fica na auditoria.
Endpoints: `denuncias` GET, `denuncias/{id}` GET, `denuncias/{id}/mensagem` e `denuncias/{id}/concluir`.
"""

import html
import time

import streamlit as st

from api_client import ApiError, concluir_denuncia, denuncia, denuncias, mensagem_denuncia
from campos import campo
from denuncias_modelo import (ABAS, RESULTADOS, TIPOS, indicadores, linhas_conversa, linhas_fila, situacao, tipo_legivel, validar_conclusao,
                              validar_mensagem)
from onboarding_modelo import data_br
from theme import alerta, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    item = st.session_state.get("den_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = denuncias(token)
    st.session_state.den_cache = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("den_modal", "den_detalhe", "den_msg", "den_res", "den_parecer"))]:
        st.session_state.pop(chave, None)


def _concluir(aviso: str) -> None:
    _fechar()
    st.session_state.pop("den_cache", None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _detalhe(denuncia_id: int) -> dict:
    """Uma chamada por abertura (cada uma fica na auditoria); guardado enquanto o modal está aberto."""
    if st.session_state.get("den_detalhe_id") != denuncia_id:
        st.session_state.den_detalhe = denuncia(st.session_state.token, denuncia_id)
        st.session_state.den_detalhe_id = denuncia_id
    return st.session_state.den_detalhe


@st.dialog("Denúncia", width="medium", on_dismiss=_fechar)
def _modal_denuncia(denuncia_id: int) -> None:
    try:
        dados = _detalhe(denuncia_id)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    d = dados.get("denuncia") or {}
    selo, tom = situacao(d.get("status"))
    quem = f"identificada: {d.get('identificacao')}" if d.get("identificada") else "anônima"
    extras = " · ".join(p for p in (f"Quando: {d['quando']}" if d.get("quando") else "", f"Envolvidos: {d['envolvidos']}" if d.get("envolvidos") else "") if p)
    st.html(f'<p class="crh-cfg-titulo">Denúncia {html.escape(d.get("protocolo") or "")}</p>'
            f'<div class="crh-pcr-topo" style="justify-content:flex-start"><span class="crh-selo {tom}">{html.escape(selo)}</span>'
            f'<span class="crh-meta">{html.escape(tipo_legivel(d.get("tipo")))} · recebida em {html.escape(data_br(d.get("recebida_em")))} · {html.escape(quem)}</span></div>'
            f'<div class="crh-cd-relato"><p class="q">Relato</p><p class="t">{html.escape(d.get("relato") or "")}</p>'
            + (f'<p class="q">{html.escape(extras)}</p>' if extras else "") + '</div>')
    if d.get("status") == "concluida":
        st.html(f'<div class="crh-lgpd-resumo"><div><span>Resultado</span><b>{html.escape(RESULTADOS.get(d.get("resultado"), "—"))}</b></div>'
                f'<div><span>Concluída em</span><b>{html.escape(data_br(d.get("concluida_em")))}</b></div></div>'
                f'<p class="crh-meta">Parecer final</p><p class="crh-lgpd-detalhe">{html.escape(d.get("parecer") or "—")}</p>')
    conversa = linhas_conversa(dados.get("mensagens") or [], para_comissao=True)
    if conversa:
        st.html("".join(f'<div class="crh-cd-msg{" meu" if not m["meu_lado"] else ""}"><p class="q">{html.escape(m["quem"])}</p><p class="t">{html.escape(m["texto"])}</p></div>'
                        for m in conversa))
    if d.get("status") == "concluida":
        return
    texto = campo(st, "Mensagem ao denunciante", "texto", "den_msg", area=True, max_chars=2000, height=90,
                  placeholder="Peça detalhes ou informe o andamento. O denunciante lê pelo código.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Concluir apuração", key="den_ir_concluir"):
            st.session_state.den_modal = ("concluir", denuncia_id)
            st.rerun()
        if st.button("Enviar mensagem", type="primary", key="den_enviar_msg"):
            erro = validar_mensagem(texto)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                mensagem_denuncia(st.session_state.token, denuncia_id, texto.strip())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Mensagem enviada. O denunciante lê pelo código.")


@st.dialog("Concluir apuração", width="medium", on_dismiss=_fechar)
def _modal_concluir(denuncia_id: int) -> None:
    resultado = st.radio("Resultado", list(RESULTADOS), format_func=RESULTADOS.get, index=None, key="den_res")
    parecer = campo(st, "Parecer final (o denunciante lê pelo código)", "texto", "den_parecer", area=True, max_chars=4000, height=110,
                    placeholder="O que foi apurado e as medidas tomadas, sem expor quem denunciou.")
    alerta(st.empty(), "atencao", "Depois de concluída, a denúncia não reabre. A identidade de quem se identificou continua só com a comissão.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="den_concluir_voltar"):
            st.session_state.den_modal = ("abrir", denuncia_id)
            st.rerun()
        if st.button("Concluir", type="primary", key="den_concluir_ok"):
            erro = validar_conclusao(resultado, parecer)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                concluir_denuncia(st.session_state.token, denuncia_id, resultado, parecer.strip())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Apuração concluída.")


def _tabela(itens: list[dict], aba: str) -> None:
    pesos = [1.6, 3.6, 1.3, 1.4, 1]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Protocolo", "Tipo e relato", "Recebida em", "Situação" if aba == "Em aberto" else "Resultado", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not itens:
            with st.container(key="rh_lin_vazio"):
                st.html(f'<p class="crh-meta">{"Nenhuma denúncia em aberto." if aba == "Em aberto" else "Nenhuma denúncia concluída ainda."}</p>')
        for i, l in enumerate(itens):
            with st.container(key=f"rh_lin_{i}" + ("_alerta" if l["destaque"] else "")):
                col = st.columns(pesos, vertical_alignment="center")
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["protocolo"])}</p><p class="d">{html.escape(l["identificacao"])}</p></div>')
                col[1].html(f'<p class="crh-doc-prazo crh-cd-resumo">{html.escape(l["pedido"])}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(l["recebida"])}</p>')
                selo, tom = l["situacao"]
                col[3].html(f'<span class="crh-selo {tom}">{html.escape(selo)}</span>', width="content")
                with col[4]:
                    if st.button("Abrir →", type="tertiary", key=f"den_abrir_{l['id']}"):
                        st.session_state.den_modal = ("abrir", l["id"])
                        st.rerun()


def pagina_denuncias() -> None:
    token = st.session_state.token
    render_topbar(st.session_state.usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Denúncias", "Só a comissão de ética vê esta fila · cada abertura fica na auditoria")
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    render_indicadores(indicadores(dados.get("contagens") or {}))
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(ABAS), default="Em aberto", required=True, key="den_aba", label_visibility="collapsed")
        st.space("stretch")
        tipo = st.selectbox("Tipo", [None] + list(TIPOS), format_func=lambda t: "Tipo: Todos" if t is None else f"Tipo: {TIPOS[t]}",
                            key="den_tipo", label_visibility="collapsed", width=260)
    _tabela(linhas_fila(dados.get("denuncias") or [], aba, tipo), aba)
    st.html('<p class="crh-meta">Ninguém da comissão vê quem enviou uma denúncia anônima. Cada abertura e cada mudança de situação ficam na auditoria.</p>')
    modal = st.session_state.get("den_modal")
    if modal:
        tipo_modal, alvo = modal
        _modal_concluir(alvo) if tipo_modal == "concluir" else _modal_denuncia(alvo)
