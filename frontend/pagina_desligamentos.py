"""
Página "Desligamentos" do RH (Figma 249:3075; change fluxo-de-desligamento; tarefa 54 de concluir-frontend-streamlit).
As decisões são só do RH (o backend recusa o Admin); ninguém decide o próprio desligamento.

Indicadores, abas (pendentes, em análise, agendados, concluídos), filtro de origem e a tabela com as ações de cada
situação: assumir a análise, aprovar (data efetiva e justificativa; imediato conclui na hora), rejeitar (motivo) e
concluir (na data efetiva, com o checklist completo). "Ver" abre o checklist de saída de um pedido aprovado, para marcar
os itens. Endpoints: `solicitacoes_desligamento` (GET, `{id}`, iniciar_analise, aprovar, rejeitar, concluir e
`checklist/{item_id}`).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import (ApiError, aprovar_desligamento, assumir_desligamento, concluir_desligamento, desligamento, desligamentos_rh,
                        marcar_checklist_desligamento, rejeitar_desligamento)
from campos import campo
from desligamento_modelo import ABAS, ETAPAS, ORIGENS, acoes_rh, faltam, indicadores, linhas_checklist, linhas_rh, validar_aprovacao
from theme import alerta, html_linha_onboarding, render_hero, render_indicadores, render_topbar

_VALIDADE_CACHE_S = 20
_ROTULOS = {"assumir": "Assumir análise", "rejeitar": "Rejeitar", "aprovar": "Aprovar", "concluir": "Concluir"}


def _guardado(chave: str, buscar):
    item = st.session_state.get(chave)
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = buscar()
    st.session_state[chave] = {"em": time.time(), "dados": dados}
    return dados


def _invalidar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith("dl_cache_")]:
        st.session_state.pop(chave, None)


def fechar() -> None:
    st.session_state.pop("dl_modal", None)
    for chave in [k for k in st.session_state if str(k).startswith(("dl_apr_", "dl_rej_"))]:
        st.session_state.pop(chave, None)


def _concluir_acao(aviso: str) -> None:
    _invalidar()
    fechar()
    st.session_state.aviso_toast = aviso
    st.rerun()


def _quadro(linha: dict) -> None:
    pares = [("Pessoa", f"{linha['pessoa']} · {linha['sub']}"), ("Origem", linha["origem"]), ("Tipo", linha["tipo"]), ("Data prevista", linha["data"])]
    campos_ = "".join(f'<p class="r">{html.escape(r)}</p><p class="v">{html.escape(v)}</p>' for r, v in pares)
    st.html(f'<div class="crh-campos crh-campos-direita">{campos_}</div>')


@st.dialog("Aprovar desligamento", width="small", on_dismiss=fechar)
def _modal_aprovar(linha: dict) -> None:
    hoje = date.today()
    _quadro(linha)
    imediato = linha.get("tipo_desligamento") == "imediato"
    sugestao = hoje if imediato else (date.fromisoformat(str(linha["data_prevista"])[:10]) if linha.get("data_prevista") else hoje)
    efetiva = st.date_input("Data efetiva (último dia)", value=max(sugestao, hoje), min_value=hoje, format="DD/MM/YYYY", key="dl_apr_data")
    motivo = campo(st, "Justificativa da decisão", "texto", "dl_apr_motivo", area=True, max_chars=1000, height=70)
    st.html('<p class="crh-meta">' + ("Imediato: o desligamento é concluído agora e o acesso da pessoa é encerrado."
                                      if imediato else "Aviso prévio: fica agendado para a data efetiva e o checklist de saída começa.") + "</p>")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="dl_apr_voltar"):
            fechar()
            st.rerun()
        if st.button("Aprovar", type="primary", key="dl_apr_ok"):
            erro = validar_aprovacao(efetiva, hoje, motivo)
            if erro:
                alerta(slot, "erro", erro)
                return
            try:
                aprovar_desligamento(st.session_state.token, linha["id"], efetiva.isoformat(), motivo.strip())
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir_acao("Desligamento concluído." if imediato else f"Desligamento agendado para {efetiva:%d/%m/%Y}. O checklist de saída começou.")


@st.dialog("Rejeitar desligamento", width="small", on_dismiss=fechar)
def _modal_rejeitar(linha: dict) -> None:
    _quadro(linha)
    motivo = campo(st, "Motivo (quem pediu vê)", "texto", "dl_rej_motivo", area=True, max_chars=1000, height=70)
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Voltar", key="dl_rej_voltar"):
            fechar()
            st.rerun()
        with st.container(key="dl_rej_perigo", width="content"):
            clicou = st.button("Rejeitar", type="primary", key="dl_rej_ok")
    if clicou:
        if len((motivo or "").strip()) < 5:
            alerta(slot, "erro", "Escreva o motivo (pelo menos 5 caracteres).")
            return
        try:
            rejeitar_desligamento(st.session_state.token, linha["id"], motivo.strip())
        except ApiError as erro:
            alerta(slot, "erro", erro.message)
            return
        _concluir_acao("Pedido rejeitado. Quem pediu foi avisado.")


def _tabela(linhas: list[dict], eu, hoje: date) -> tuple[str | None, dict | None]:
    pesos = [2.3, 1.1, 1.5, 1.1, 1.5, 1.9]
    clicado = (None, None)
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Pessoa", "Origem", "Tipo", "Data prevista", "Responsável RH", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        if not linhas:
            with st.container(key="rh_lin_vazio"):
                st.html('<p class="crh-meta">Nenhum pedido nesta aba.</p>')
        for i, l in enumerate(linhas):
            with st.container(key=f"rh_lin_{i}"):
                c = st.columns(pesos, vertical_alignment="center")
                c[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(l["pessoa"])}</p><p class="d">{html.escape(l["sub"])}</p></div>')
                for coluna, texto in zip(c[1:5], (l["origem"], l["tipo"], l["data"], l["responsavel"])):
                    coluna.html(f'<p class="crh-doc-prazo">{html.escape(texto)}</p>')
                with c[5]:
                    with st.container(horizontal=True, horizontal_alignment="right"):
                        if l["status"] in ("agendado", "concluido") and st.button("Ver", type="tertiary", key=f"dl_ver_{l['id']}"):
                            clicado = ("ver", l)
                        acoes = acoes_rh(l, eu, hoje)
                        if not acoes and l["status"] not in ("agendado", "concluido"):
                            st.html(f'<span class="crh-selo {l["tom"]}">{html.escape(l["badge"])}</span>', width="content")
                        for acao, motivo in acoes.items():
                            if st.button(_ROTULOS[acao], type="tertiary", key=f"dl_{acao}_{l['id']}", disabled=motivo is not None, help=motivo):
                                clicado = (acao, l)
    return clicado


def _checklist(token: str, linha: dict, eu) -> None:
    try:
        detalhe = _guardado(f"dl_cache_det_{linha['id']}", lambda: desligamento(token, linha["id"]))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    itens = detalhe.get("checklist") or []
    st.html(f'<p class="crh-cfg-titulo">Checklist de saída — {html.escape(linha["pessoa"])}</p>'
            + ('<p class="crh-meta">Pedido aprovado antes do checklist: sem itens.</p>' if not itens
               else f'<p class="crh-meta">Faltam {faltam(itens)} de {len(itens)}. Concluir exige todos feitos.</p>' if faltam(itens)
               else '<p class="crh-meta">Tudo feito.</p>'))
    proprio = linha.get("colaborador_user_id") == eu
    for item in linhas_checklist(itens):
        with st.container(horizontal=True, vertical_alignment="center", key=f"dl_item_{item['id']}"):
            st.html(html_linha_onboarding(item["titulo"], item["detalhe"], item["badge"], item["tom"]))
            if not proprio and st.button("Desfazer" if item["feito"] else "Marcar feito", key=f"dl_marcar_{item['id']}"):
                try:
                    marcar_checklist_desligamento(token, linha["id"], item["id"], not item["feito"])
                except ApiError as erro:
                    alerta(st.empty(), "erro", erro.message)
                    return
                st.session_state.pop(f"dl_cache_det_{linha['id']}", None)
                st.rerun()


def pagina_desligamentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Desligamentos", "Pedidos de colaboradores e gestores, da análise ao último dia")
    if str(usuario.get("perfil", "")).upper() != "RH":
        alerta(st.empty(), "erro", "Os desligamentos são decididos só pelo RH." if str(usuario.get("perfil", "")).upper() == "ADMIN" else "Esta tela é só do RH.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _guardado("dl_cache_lista", lambda: desligamentos_rh(token))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    hoje = date.today()
    eu = usuario.get("id")
    render_indicadores(indicadores(dados.get("contagens")))
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", list(ABAS), default="Pendentes", required=True, key="dl_aba", label_visibility="collapsed")
        st.space("stretch")
        origem = st.selectbox("Origem", [None] + list(ORIGENS), format_func=lambda o: "Origem: Todos" if o is None else f"Origem: {ORIGENS[o]}",
                              key="dl_origem", label_visibility="collapsed", width=200)
    linhas = linhas_rh(dados.get("solicitacoes"), aba, origem)
    acao, linha = _tabela(linhas, eu, hoje)
    if acao == "ver":
        st.session_state.dl_ver = linha["id"]
        st.rerun()
    if acao == "assumir":
        try:
            assumir_desligamento(token, linha["id"])
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        _concluir_acao(f"Você assumiu a análise do pedido de {linha['pessoa']}.")
    if acao == "concluir":
        try:
            concluir_desligamento(token, linha["id"])
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        _concluir_acao(f"Desligamento de {linha['pessoa']} concluído.")
    if acao in ("aprovar", "rejeitar"):
        st.session_state.dl_modal = (acao, linha["id"])
        st.rerun()

    esquerda, direita = st.columns([1.6, 1], gap="medium")
    escolhido = next((l for l in linhas_rh(dados.get("solicitacoes"), "Agendados") + linhas_rh(dados.get("solicitacoes"), "Concluídos")
                      if l["id"] == st.session_state.get("dl_ver")), None)
    with esquerda:
        with st.container(key="cfg_card_dl_checklist"):
            if escolhido and escolhido["status"] in ("agendado", "concluido"):
                _checklist(token, escolhido, eu)
            else:
                st.html('<p class="crh-cfg-titulo">Checklist de saída</p><p class="crh-meta">Aparece depois de aprovado. Clique em "Ver" num pedido agendado ou concluído.</p>')
    with direita:
        st.html(f'<div class="crh-painel crh-bloco"><p class="crh-cfg-titulo">Etapas</p><p class="crh-meta">{html.escape(ETAPAS)}</p></div>')

    modal = st.session_state.get("dl_modal")
    if modal:
        tipo, alvo = modal
        alvo_linha = next((l for l in linhas_rh(dados.get("solicitacoes"), "Em análise") if l["id"] == alvo), None)
        if alvo_linha is None:
            fechar()
        elif tipo == "aprovar":
            _modal_aprovar(alvo_linha)
        else:
            _modal_rejeitar(alvo_linha)
